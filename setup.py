#!/usr/bin/env python3

import hashlib
import http
import io
import os.path
import stat
import sys
import tarfile
import urllib.request
import zipfile
from distutils.command.build import build as orig_build
from distutils.core import Command

from setuptools import setup
from setuptools.command.install import install as orig_install


CIRCLECI_CLI_VERSION = "0.1.15149"
ARCHIVE_SHA256 = {
    "linux": (
        "circleci-cli_0.1.15149_linux_amd64.tar.gz",
        "2e61afee948454358028f3b65850f5e61b6d2ce81d0b6b7f0c8621a708759dea",
    ),
    "darwin": (
        "circleci-cli_0.1.15149_darwin_amd64.tar.gz",
        "d6e481ba00851268ed84a9b37613ccfa4d1ec07089c6be1e4896a2c1384b8d15",
    ),
    "win32": (
        "circleci-cli_0.1.15149_windows_amd64.zip",
        "5d4de753045d10b905fb93b0c5dfd05cb0ee60e315507210377efa031a9574fd",
    ),
}


def get_download_url() -> str:
    archive, sha256 = ARCHIVE_SHA256[sys.platform]
    url = (
        f"https://github.com/CircleCI-Public/circleci-cli/releases/download/"
        f"v{CIRCLECI_CLI_VERSION}/{archive}"
    )
    return url, sha256


def download(url: str, sha256: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        code = resp.getcode()
        if code != http.HTTPStatus.OK:
            raise ValueError(f"HTTP failure. Code: {code}")
        data = resp.read()

    checksum = hashlib.sha256(data).hexdigest()
    if checksum != sha256:
        raise ValueError(f"sha256 mismatch, expected {sha256}, got {checksum}")

    return data


def extract(url: str, data: bytes) -> bytes:
    with io.BytesIO(data) as bio:
        if ".tar." in url:
            with tarfile.open(fileobj=bio) as tarf:
                for info in tarf.getmembers():
                    if info.isfile() and info.name.endswith("circleci"):
                        return tarf.extractfile(info).read()
        elif url.endswith(".zip"):
            with zipfile.ZipFile(bio) as zipf:
                for info in zipf.infolist():
                    if info.filename.endswith(".exe"):
                        return zipf.read(info.filename)

    raise AssertionError(f"unreachable {url}")


def save_executable(data: bytes, base_dir: str):
    exe = "circleci" if sys.platform != "win32" else "circleci.exe"
    output_path = os.path.join(base_dir, exe)
    os.makedirs(base_dir)

    with open(output_path, "wb") as fp:
        fp.write(data)

    # Mark as executable.
    # https://stackoverflow.com/a/14105527
    mode = os.stat(output_path).st_mode
    mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(output_path, mode)


class build(orig_build):
    sub_commands = orig_build.sub_commands + [("fetch_binaries", None)]


class install(orig_install):
    sub_commands = orig_install.sub_commands + [("install_circleci_cli", None)]


class fetch_binaries(Command):
    build_temp = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.set_undefined_options("build", ("build_temp", "build_temp"))

    def run(self):
        # save binary to self.build_temp
        url, sha256 = get_download_url()
        archive = download(url, sha256)
        data = extract(url, archive)

        save_executable(data, self.build_temp)


class install_circleci_cli(Command):
    description = "install the shellcheck executable"
    outfiles = ()
    build_dir = install_dir = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        # this initializes attributes based on other commands' attributes
        self.set_undefined_options("build", ("build_temp", "build_dir"))
        self.set_undefined_options(
            "install",
            ("install_scripts", "install_dir"),
        )

    def run(self):
        self.outfiles = self.copy_tree(self.build_dir, self.install_dir)

    def get_outputs(self):
        return self.outfiles


command_overrides = {
    "install": install,
    "install_circleci_cli": install_circleci_cli,
    "build": build,
    "fetch_binaries": fetch_binaries,
}


try:
    from wheel.bdist_wheel import bdist_wheel as orig_bdist_wheel

    class bdist_wheel(orig_bdist_wheel):
        def finalize_options(self):
            orig_bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package
            self.root_is_pure = False

        def get_tag(self):
            _, _, plat = orig_bdist_wheel.get_tag(self)
            # We don't contain any python source, nor any python extensions
            return "py2.py3", "none", plat

    command_overrides["bdist_wheel"] = bdist_wheel
except ImportError:
    pass

setup(version=f"{CIRCLECI_CLI_VERSION}", cmdclass=command_overrides)
