#!/bin/sh
# Copies a freshly built ROM into roms/<N>.0/, creating the next numbered folder.
# Called by test/pipeline.sh (via the Makefile) after every non-compare ROM build.
#   version_rom.sh <rom> [<report dir>] [--untested]
# <report dir>: test report (relatorio.html, img/, meta.json) copied into the version folder.
# --untested: the tests did not run; marks the version with NAO_TESTADA.txt.
set -e

rom="$1"
dir=roms

dir=${ESTEIRA_ROMS_DIR:-$dir}
mkdir -p "$dir"
last=$(ls -1 "$dir" | sed -n 's/^\([0-9][0-9]*\)\.0$/\1/p' | sort -n | tail -n 1)
next=$(( ${last:-0} + 1 ))

mkdir -p "$dir/$next.0"
cp "$rom" "$dir/$next.0/"

shift
report=""
untested=0
for arg in "$@"; do
    if [ "$arg" = "--untested" ]; then untested=1; else report="$arg"; fi
done
if [ -n "$report" ]; then
    for item in relatorio.html img meta.json; do
        if [ -e "$report/$item" ]; then cp -r "$report/$item" "$dir/$next.0/"; fi
    done
fi
if [ "$untested" = 1 ]; then
    echo "ROM nao testada: a esteira de testes foi pulada (SKIP_TESTS=1)." > "$dir/$next.0/NAO_TESTADA.txt"
fi
echo "Versioned $rom -> $dir/$next.0/"
