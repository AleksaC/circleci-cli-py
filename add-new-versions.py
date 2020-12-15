#!/usr/bin/env python
import json
import os
import re
from typing import List

from urllib.request import Request
from urllib.request import urlopen


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


def update_version(version: str) -> None:
    with open("setup.py", "r+") as f:
        validator = f.read()
        f.seek(0)
        f.write(
            re.sub(r"CIRCLECI_CLI_VERSION = \"\d+\.\d+.\d+\"\n", f'CIRCLECI_CLI_VERSION = "{version}"\n', validator)
        )
        f.truncate()


def push_tag(version: str) -> None:
    os.system(f"./tag.sh {version}")


if __name__ == "__main__":
    releases = get_releases()
    for release in reversed(releases):
        print(f"Adding new release: {release}")
        update_version(release.replace("v", ""))
        # TODO: Update checksums
        push_tag(release)
