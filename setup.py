#!/usr/bin/env python3

import hashlib
import http
import io
import os.path
import platform
import stat
import tarfile
import urllib.request
import zipfile
from distutils.command.build import build as orig_build
from distutils.core import Command

from setuptools import setup
from setuptools.command.install import install as orig_install


VERSION = "0.1.32323"
ARCHIVE_SHA256 = {'windows_arm64': ('circleci-cli_0.1.32323_windows_arm64.zip', '086ed4cb5413e534083a3b9fa5f75e7f7282c5eb0e04a718dfbe21e84d0bf49d'), 'linux_arm64': ('circleci-cli_0.1.32323_linux_arm64.tar.gz', '5d14e8e9531d060178ef66ff1cbbf1f60dda792ce478fc0fc627a727f4bb8361'), 'windows_amd64': ('circleci-cli_0.1.32323_windows_amd64.zip', '6fef8f41ebdfd5c1e82cb1dee1913a58a27193ba269ac96f8d9febf0ebd217ef'), 'darwin_amd64': ('circleci-cli_0.1.32323_darwin_amd64.tar.gz', 'b4ffaed6fb0a7e642e91325b2d72885fe176fcd1230376eb95a37da0fca3bbdc'), 'linux_amd64': ('circleci-cli_0.1.32323_linux_amd64.tar.gz', 'd4f24aa458bfccd8b58c2f5b9abd3004f7d819f1ab644f5e6dd54e0a3e839926'), 'darwin_arm64': ('circleci-cli_0.1.32323_darwin_arm64.tar.gz', 'f6d15ce07fabe084a8986dd89c142efe01427685bb93e04c706e1e4940e0ecff')}
RELEASES_BASE_URL = "https://github.com/CircleCI-Public/circleci-cli/releases/download"


def get_download_url() -> str:
    os, arch = platform.system().lower(), platform.machine().lower()
    if (
        os == "windows"
        or "x86" in arch
        or "amd" in arch
        or "i386" in arch
        or "i686" in arch
    ):
        arch = "amd"
    elif "arm" in arch or arch == "aarch64":
        arch = "arm"

    archive, sha256 = ARCHIVE_SHA256[f"{os}_{arch}64"]
    url = f"{RELEASES_BASE_URL}/v{VERSION}/{archive}"

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
                    if not info.is_dir() and (
                        info.filename.endswith(".exe")
                        or info.filename.endswith("circleci")
                    ):
                        return zipf.read(info.filename)

    raise AssertionError(f"unreachable {url}")


def save_executable(data: bytes, base_dir: str):
    exe = "circleci" if platform.system() != "Windows" else "circleci.exe"
    output_path = os.path.join(base_dir, exe)
    os.makedirs(base_dir, exist_ok=True)

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
    sub_commands = orig_install.sub_commands + [("install_circleci", None)]


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


class install_circleci(Command):
    description = "install the circleci executable"
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
    "install_circleci": install_circleci,
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

setup(version=f"{VERSION}", cmdclass=command_overrides)
