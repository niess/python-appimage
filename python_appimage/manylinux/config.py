from enum import auto, Enum
import platform
from typing import NamedTuple, Union


__all__ = ['Arch', 'PythonImpl', 'PythonVersion']


class Arch(Enum):
    '''Supported platform architectures.'''
    AARCH64 = auto()
    I686 = auto()
    X86_64 = auto()

    def __str__(self):
        return self.name.lower()

    @classmethod
    def from_host(cls) -> 'Arch':
        return cls.from_str(platform.machine())

    @classmethod
    def from_str(cls, value) -> 'Arch':
        for arch in cls:
            if value == str(arch):
                return arch
        else:
            raise NotImplementedError(value)


class LinuxTag(Enum):
    '''Supported platform tags.'''
    MANYLINUX_1 = auto()
    MANYLINUX_2010 = auto()
    MANYLINUX_2014 = auto()
    MANYLINUX_2_24 = auto()
    MANYLINUX_2_28 = auto()

    def __str__(self):
        tag = self.name.lower()
        if self in (LinuxTag.MANYLINUX_1, LinuxTag.MANYLINUX_2010,
                    LinuxTag.MANYLINUX_2014):
            return tag.replace('_', '')
        else:
            return tag

    @classmethod
    def from_str(cls, value) -> 'LinuxTag':
        for tag in cls:
            if value == str(tag):
                return tag
        else:
            raise NotImplementedError(value)


class PythonImpl(Enum):
    '''Supported Python implementations.'''
    CPYTHON = auto()


class PythonVersion(NamedTuple):
    ''''''

    major: int
    minor: int
    patch: Union[int, str]

    @classmethod
    def from_str(cls, value: str) -> 'PythonVersion':
        major, minor, patch = value.split('.', 2)
        try:
            patch = int(patch)
        except ValueError:
            pass
        return cls(int(major), int(minor), patch)

    def long(self) -> str:
        return f'{self.major}.{self.minor}.{self.patch}'

    def short(self) -> str:
        return f'{self.major}.{self.minor}'
