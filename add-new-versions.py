#!/usr/bin/env python

import os
import re
from typing import List

import requests


def get_releases() -> List[str]:
    base_url = "https://api.github.com/repos/{}/{}/{}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    circleci_cli_releases = requests.get(
        base_url.format("CircleCI-Public", "circleci-cli", "releases"), headers=headers
    )

    hook_tags = requests.get(
        base_url.format("AleksaC", "circleci-validation-pre-commit", "tags"),
        headers=headers,
    )

    new_releases = []

    if circleci_cli_releases.ok and hook_tags.ok:
        latest = hook_tags.json()[0]["name"]
        for release in circleci_cli_releases.json():
            version = release["tag_name"]
            if version == latest:
                break
            new_releases.append(version)

    return new_releases


def update_version(version: str) -> None:
    with open("validate.sh", "r+") as f:
        validator = f.read()
        f.seek(0)
        f.write(
            re.sub(r"VERSION=\"\d+\.\d+.\d+\"\n", f'VERSION="{version}"\n', validator)
        )
        f.truncate()


def push_tag(version: str) -> None:
    os.system(f"./tag.sh {version}")


if __name__ == "__main__":
    releases = get_releases()
    for release in reversed(releases):
        print(f"Adding new release: {release}")
        update_version(release)
        push_tag(release)
