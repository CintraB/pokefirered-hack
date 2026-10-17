#!/bin/sh
# Copies a freshly built ROM into roms/<N>.0/, creating the next numbered folder.
# Called by the Makefile after every non-compare ROM build.
set -e

rom="$1"
dir=roms

# Test builds (make ... TESTBUILD=1) carry the test hooks and are never versioned.
case "$rom" in
    *_test.gba) echo "Not versioning test build $rom"; exit 0 ;;
esac

mkdir -p "$dir"
last=$(ls -1 "$dir" | sed -n 's/^\([0-9][0-9]*\)\.0$/\1/p' | sort -n | tail -n 1)
next=$(( ${last:-0} + 1 ))

mkdir -p "$dir/$next.0"
cp "$rom" "$dir/$next.0/"
echo "Versioned $rom -> $dir/$next.0/"
