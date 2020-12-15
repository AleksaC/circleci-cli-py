#!/usr/bin/env python

import ast
import io
import json
import os
import re
import tokenize
from urllib.request import Request
from urllib.request import urlopen

from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple
from typing import Union


def get(url: str, headers: dict) -> dict:
    req = Request(url, headers=headers)
    resp = urlopen(req, timeout=30)
    return json.loads(resp.read())


def get_releases() -> List[str]:
    base_url = "https://api.github.com/repos/{}/{}/{}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    circleci_cli_releases = get(
        base_url.format("CircleCI-Public", "circleci-cli", "releases"), headers=headers
    )

    hook_tags = get(
        base_url.format("AleksaC", "circleci-validation-pre-commit", "tags"),
        headers=headers,
    )

    new_releases = []
    latest = hook_tags[0]["name"]
    for release in circleci_cli_releases:
        version = release["tag_name"]
        if version == latest:
            break
        new_releases.append(version)

    return new_releases


def get_checksums(version: str) -> dict:
    checksum_url = (
        f"https://github.com/CircleCI-Public/circleci-cli/releases/download/"
        f"v{version}/circleci-cli_{version}_checksums.txt"
    )

    req = Request(checksum_url)
    resp = urlopen(req, timeout=30)
    checksums = resp.read().decode()

    checksum_re = re.compile(
        r"(?P<sha>[A-Fa-f0-9]{64})  "
        r"(?P<file>circleci-cli_[0-9]+\.[0-9]+\.[0-9]+_"
        r"(?P<platform>darwin|windows|linux)_amd64(\.tar\.gz|\.zip))\n"
    )

    archive_sha = {}

    for match in re.findall(checksum_re, checksums):
        sha, archive, platform, _ = match
        archive_sha[platform] = (archive, sha)

    return archive_sha


def update_file(
    file_path: str, replacements: Iterable[Tuple[Union[re.Pattern, str], str]]
) -> None:
    with open(file_path, "r+") as f:
        old = f.read()
        new = old
        for pattern, replacement in replacements:
            new = re.sub(
                pattern,
                replacement,
                new,
            )
        f.seek(0)
        f.write(new)
        f.truncate()


def update_file_tokenize(file_path: str) -> str:
    with open(file_path, "r+") as f:
        contents = io.StringIO(f.read())
        tokens = tokenize.generate_tokens(contents.readline)
        lines = []
        while True:
            token = next(tokens)
            if token.type == 1 and token.string == "ARCHIVE_SHA256":
                while True:
                    lines.append(token.line)
                    next_token = next(tokens)
                    while next_token.line == token.line:
                        next_token = next(tokens)
                    token = next_token
                    if token.type == 54 and token.string == "}":
                        lines.append(token.string)
                        return "".join(lines)


def update_archive_sha(version: str) -> None:
    archive_sha256_str = update_file_tokenize("setup.py")
    archive_sha256_dict: Dict[str, Tuple[str, str]] = ast.literal_eval(
        archive_sha256_str[archive_sha256_str.find("{") :]
    )
    checksums = get_checksums(version)

    archive_sha256_new = archive_sha256_str
    for platform in checksums:
        old_archive, old_sha = archive_sha256_dict[
            "win32" if platform == "windows" else platform
        ]
        new_archive, new_sha = checksums[platform]

        archive_sha256_new = archive_sha256_new.replace(old_archive, new_archive)
        archive_sha256_new = archive_sha256_new.replace(old_sha, new_sha)

    with open("setup.py", "r+") as f:
        contents = f.read()
        f.seek(0)
        f.write(contents.replace(archive_sha256_str, archive_sha256_new))
        f.truncate()


def update_version(version: str) -> None:
    update_archive_sha(version)
    update_file(
        "setup.py",
        [
            (
                r"CIRCLECI_CLI_VERSION = \"[0-9]+\.[0-9]+\.[0-9]+\"\n",
                f'CIRCLECI_CLI_VERSION = "{version}"\n',
            )
        ],
    )
    update_file(
        "README.md",
        [
            (r"rev: v[0-9]+\.[0-9]+\.[0-9]+", f"rev: v{version}"),
            (r"@v[0-9]+\.[0-9]+\.[0-9]+", f"@v{version}"),
        ],
    )


def push_tag(version: str) -> None:
    os.system(f"./tag.sh {version}")


if __name__ == "__main__":
    releases = get_releases()

    for release in reversed(releases):
        print(f"Adding new release: {release}")
        update_version(release.replace("v", ""))
        push_tag(release)
