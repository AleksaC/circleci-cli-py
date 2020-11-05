#!/usr/bin/env bash

set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BINARY="${DIR}/circleci"
ARCHIVE="${BINARY}.tar.gz"
VERSION="0.1.11458"

BASE_URL="https://github.com/CircleCI-Public/circleci-cli/releases/download/v${VERSION}"
case $OSTYPE in
    "linux-gnu")
        URL="${BASE_URL}/circleci-cli_${VERSION}_linux_amd64.tar.gz"
        ;;
    "darwin")
        URL="${BASE_URL}/circleci-cli_${VERSION}_darwin_amd64.tar.gz"
        ;;
    "msys")
        URL="${BASE_URL}/circleci-cli_${VERSION}_windows_amd64.zip"
        ARCHIVE="${BINARY}.zip"
        ;;
esac

if [ ! -f "$BINARY" ] && [ ! -f "$ARCHIVE" ]; then
    echo -e "\nDownloading CircleCI CLI...\n"
    if command -v curl >/dev/null 2>&1 ; then
        curl -L $URL -o "$ARCHIVE" -s
    elif command -v wget >/dev/null 2>&1; then
        wget -O "$ARCHIVE" $URL &> /dev/null
    else
        echo "Please install wget or curl, or manually download ${URL} to ${DIR}."
        exit 1
    fi
fi

if [ ! -f "$BINARY" ]; then
    if [ "$OSTYPE" = "msys" ];
    then
        unzip -j $ARCHIVE -x "*LICENSE" -d "$DIR"
        BINARY="$BINARY.exe"
    else
        tar xzf "$ARCHIVE" --strip=1 -C "$DIR"
    fi
fi

if [ ! -x BINARY ]; then
    chmod +x "$BINARY"
fi

if ! eMSG=$("$BINARY" config validate -c $1); then
    echo "CircleCI Configuration Failed Validation."
    echo "$eMSG"
    exit 1
fi
