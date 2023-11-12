#! /usr/bin/env python3
import argparse
from collections import defaultdict
from dataclasses import dataclass
import os
import subprocess
import sys
from typing import Optional

from github import Auth, Github

from python_appimage.commands.build.manylinux import execute as build_manylinux
from python_appimage.commands.list import execute as list_pythons
from python_appimage.utils.log import log
from python_appimage.utils.manylinux import format_appimage_name, format_tag


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

    ref: Optional["github.GitRef"] = None
    release: Optional["github.GitRelease"] = None

    def message(self):
        '''Returns release message'''
        return f'Appimage distributions of {self.title()} (see `Assets` below)'

    def title(self):
        '''Returns release title'''
        version = self.tag[6:]
        return f'Python {version}'


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

    def formated_tag(self):
        '''Returns formated manylinux tag'''
        return format_tag(self.tag)

    def previous_version(self):
        '''Returns previous version'''
        if self.asset:
            return self.asset.name[6:-9].split('-', 1)[0]

    def release_tag(self):
        '''Returns release git tag'''
        version = self.version.rsplit('.', 1)[0]
        return f'python{version}'


def update(args):
    '''Update Python AppImage GitHub releases
    '''

    sha = args.sha
    if sha is None:
        sha = os.getenv('GITHUB_SHA')
        if sha is None:
            p = subprocess.run(
                'git rev-parse HEAD',
                shell = True,
                capture_output = True,
                check = True
            )
            sha = p.stdout.decode().strip()

    # Connect to GitHub
    token = args.token
    if token is None:
        # First, check for token in env
        token = os.getenv('GITHUB_TOKEN')
        if token is None:
            # Else try to get a token from gh app
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
            meta = ReleaseMeta(
                tag = release.tag_name,
                release = release
            )
            ref = repo.get_git_ref(f'tags/{meta.tag}')
            if (ref.ref is not None) and (ref.object.sha != sha):
                meta.ref = ref
            releases[release.tag_name] = meta

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

                if (meta is None) or (meta.version != version) or args.all:
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

    if args.dry:
        # Log foreseen changes and exit
        for tag in new_releases:
            meta = ReleaseMeta(tag)
            log('DRY', f'new release for {meta.title()}')

        for meta in new_assets:
            log('DRY', f'create asset {meta.appimage_name()}')
            if meta.asset is not None:
                log('DRY', f'remove asset {meta.asset.name}')

        for meta in releases.values():
            if meta.ref is not None:
                log('DRY', f'refs/tags/{meta.tag} -> {sha}')
                if meta.release is not None:
                    log('DRY', f'reformat release for {meta.title()}')

        if new_assets:
            log('DRY', f'new update summary with {len(new_assets)} entries')

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
            message = meta.message(),
            prerelease = True
        )
        releases[tag] = meta
        log('UPDATE', f'new release for {title}')

    # Update assets.
    update_summary = []
    for meta in new_assets:
        release = releases[meta.release_tag()].release
        appimage = meta.appimage_name()
        new_asset = release.upload_asset(
            path = f'{APPIMAGES_DIR}/{appimage}',
            name = appimage
        )
        if meta.asset:
            meta.asset.delete_asset()
            update_summary.append(
                f'- update {meta.formated_tag()}/{meta.abi} '
                    f'{meta.previous_version()} -> {meta.version}'
            )
        else:
            update_summary.append(
                f'- add {meta.formated_tag()}/{meta.abi} {meta.version}'
            )

        meta.asset = new_asset
        assets[meta.tag][meta.abi] = meta

    # Update git tags SHA
    for meta in releases.values():
        if meta.ref is not None:
            meta.ref.edit(
                sha = sha,
                force = True
            )
            log('UPDATE', f'refs/tags/{meta.tag} -> {sha}')

            if meta.release is not None:
                title = meta.title()
                meta.release.update_release(
                    name = title,
                    message = meta.message(),
                    prerelease = True,
                    tag_name = meta.tag
                )
                log('UPDATE', f'reformat release for {title}')

    # Generate update summary
    if update_summary:
        for release in repo.get_releases():
            if release.tag_name == 'update-summary':
                release.delete_release()
                break

        message = os.linesep.join(update_summary)
        repo.create_git_release(
            tag = 'update-summary',
            name = 'Update summary',
            message = message,
            prerelease = True
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = 'Update GitHub releases of Python AppImages'
    )
    parser.add_argument('-a', '--all',
        help = 'force update of all available releases',
        action = 'store_true',
        default = False
    )
    parser.add_argument('-d', '--dry',
        help = 'dry run (only log changes)',
        action = 'store_true',
        default = False
    )
    parser.add_argument("-s", "--sha",
        help = "reference commit SHA"
    )
    parser.add_argument('-t', '--token',
        help = 'GitHub authentication token'
    )

    args = parser.parse_args()
    sys.argv = sys.argv[:1] # Empty args for fake call
    update(args)
