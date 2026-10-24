#!/bin/sh
# Convenience wrapper for this workstation; normal Git works after installing Git LFS.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
if [ -d "$root/../.tools/bin" ]; then PATH="$root/../.tools/bin:$PATH"; export PATH; fi
exec git -C "$root" "$@"
