#! /usr/bin/env python3
import argparse
from collections import defaultdict
from dataclasses import dataclass
import os
import subprocess
from typing import Optional

from github import Auth, Github

from python_appimage.commands.build.manylinux import execute as build_manylinux
from python_appimage.commands.list import execute as list_pythons
from python_appimage.utils.log import log
from python_appimage.utils.manylinux import format_appimage_name


# Build matrix
ARCHS = ('x86_64', 'i686')
MANYLINUSES = ('1', '2010', '2014', '2_24', '2_28')
EXCLUDES = ('2_28_i686',)

# Build directory for AppImages
APPIMAGES_DIR = 'build-appimages'


@dataclass
class ReleaseMeta:
    '''Metadata relative to a GitHub release
    '''

    tag: str

    release: Optional["github.GitRelease"] = None

    def title(self):
        '''Returns release title'''
        version = self.tag[6:]
        return f'Python {version}'


@dataclass
class TagMeta:
    '''Metadata relative to a git tag
    '''

    tag: str
    ref: "github.GitRef"


@dataclass
class AssetMeta:
    '''Metadata relative to a release Asset
    '''

    tag: str
    abi: str
    version: str

    asset: Optional["github.GitReleaseAsset"] = None

    @classmethod
    def from_appimage(cls, name):
        '''Returns an instance from a Python AppImage name
        '''
        tmp = name[6:-9]
        tmp, tag = tmp.split('-manylinux', 1)
        if tag.startswith('_'):
            tag = tag[1:]
        version, abi = tmp.split('-', 1)
        return cls(
            tag = tag,
            abi = abi,
            version = version
        )

    def appimage_name(self):
        '''Returns Python AppImage name'''
        return format_appimage_name(self.abi, self.version, self.tag)

    def release_tag(self):
        '''Returns release git tag'''
        version = self.version.rsplit('.', 1)[0]
        return f'python{version}'


def update(args):
    '''Update Python AppImage GitHub releases
    '''

    # Connect to GitHub
    if args.token is None:
        # Get token from gh app (e.g. for local runs)
        p = subprocess.run(
            'gh auth token',
            shell = True,
            capture_output = True,
            check = True
        )
        token = p.stdout.decode().strip()

    auth = Auth.Token(token)
    session = Github(auth=auth)
    repo = session.get_repo('niess/python-appimage')

    # Fetch currently released AppImages
    log('FETCH', 'currently released AppImages')
    releases = {}
    assets = defaultdict(dict)
    n_assets = 0
    for release in repo.get_releases():
        if release.tag_name.startswith('python'):
            releases[release.tag_name] = ReleaseMeta(
                tag = release.tag_name,
                release = release
            )
            for asset in release.get_assets():
                if asset.name.endswith('.AppImage'):
                    n_assets += 1
                    meta = AssetMeta.from_appimage(asset.name)
                    assert(meta.release_tag() == release.tag_name)
                    meta.asset = asset
                    assets[meta.tag][meta.abi] = meta

    n_releases = len(releases)
    log('FETCH', f'found {n_assets} AppImages in {n_releases} releases')

    # Look for updates.
    new_releases = set()
    new_assets = []
    new_sha = []

    for manylinux in MANYLINUSES:
        for arch in ARCHS:
            tag = f'{manylinux}_{arch}'
            if tag in EXCLUDES:
                continue

            pythons = list_pythons(tag)
            for (abi, version) in pythons:
                try:
                    meta = assets[tag][abi]
                except KeyError:
                    meta = None

                if meta is None or meta.version != version:
                    new_meta = AssetMeta(
                        tag = tag,
                        abi = abi,
                        version = version
                    )
                    if meta is not None:
                        new_meta.asset = meta.asset
                    new_assets.append(new_meta)

                    rtag = new_meta.release_tag()
                    if rtag not in releases:
                        new_releases.add(rtag)

    # Check SHA of tags.
    p = subprocess.run(
        'git rev-parse HEAD',
        shell = True,
        capture_output = True,
        check = True
    )
    sha = p.stdout.decode().strip()

    for tag in releases.keys():
        ref = repo.get_git_ref(f'tags/{tag}')
        if ref.ref is not None:
            if ref.object.sha != sha:
                meta = TagMeta(
                    tag = tag,
                    ref = ref
                )
                new_sha.append(meta)

    # Log foreseen changes.
    for tag in new_releases:
        meta = ReleaseMeta(tag)
        log('FORESEEN', f'create new release for {meta.title()}')

    for meta in new_assets:
        log('FORESEEN', f'create asset {meta.appimage_name()}')
        if meta.asset:
            log('FORESEEN', f'remove asset {meta.asset.name}')

    for meta in new_sha:
        log('FORESEEN', f'update git SHA for refs/tags/{meta.tag}')

    if args.dry:
        return

    if new_assets:
        # Build new AppImage(s)
        cwd = os.getcwd()
        os.makedirs(APPIMAGES_DIR, exist_ok=True)
        try:
            os.chdir(APPIMAGES_DIR)
            for meta in new_assets:
                build_manylinux(meta.tag, meta.abi)
        finally:
            os.chdir(cwd)

    # Create any new release(s).
    for tag in new_releases:
        meta = ReleaseMeta(tag)
        title = meta.title()
        meta.release = repo.create_git_release(
            tag = meta.tag,
            name = title,
            message = f'Appimage distributions of {title} (see `Assets` below)',
            prerelease = True
        )
        releases[tag] = meta

    # Update assets.
    for meta in new_assets:
        release = releases[meta.release_tag()].release
        appimage = meta.appimage_name()
        new_asset = release.upload_asset(
            path = f'{APPIMAGES_DIR}/{appimage}',
            name = appimage
        )
        if meta.asset:
            meta.asset.delete_asset()
        meta.asset = new_asset
        assets[meta.tag][meta.abi] = meta

    # Update git tags SHA.
    for meta in new_sha:
        meta.ref.edit(
            sha = sha,
            force = True
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = 'Update GitHub releases of Python AppImages'
    )
    parser.add_argument('-d', '--dry',
        help = 'dry run (only log changes)',
        action = 'store_true',
        default = False
    )
    parser.add_argument('-t', '--token',
        help = 'GitHub authentication token'
    )

    # XXX Add --all arg

    args = parser.parse_args()
    update(args)
