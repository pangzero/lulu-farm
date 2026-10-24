#!/bin/sh
set -eu
if [ "$#" -ne 2 ]; then
    echo 'Usage: encode-vfr-recording.sh RECORDING_DIRECTORY NEW_OUTPUT.mp4' >&2
    exit 2
fi
tool_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir=$(mktemp -d "${TMPDIR:-/tmp}/lulu-vfr.XXXXXX")
module_cache="${TMPDIR:-/tmp}/lulu-farm-swift-module-cache"
trap 'rm -rf "$build_dir"' EXIT HUP INT TERM
# System developer tools and frameworks only: no package installation/download.
/usr/bin/xcrun swiftc -O -module-cache-path "$module_cache" \
    "$tool_dir/encode-vfr-recording.swift" -o "$build_dir/encode-vfr-recording"
"$build_dir/encode-vfr-recording" "$1" "$2"
