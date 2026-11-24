#!/bin/sh
# POSIX helper for an unused review environment; no installs, global version edits, or shell activation.
set -eu
if [ "$#" -ne 2 ]; then
    echo "Usage: sh research/footprint/venv311.sh runtime|research NEW_PATH" >&2
    exit 2
fi
case "$1" in runtime|research) ;; *) echo "Choose runtime or research." >&2; exit 2;; esac
mode=$1
dest=$2
if [ -z "$dest" ] || [ -e "$dest" ] || [ -L "$dest" ]; then
    echo "Choose a new environment path; an existing environment is never overwritten." >&2
    exit 2
fi
valid311() {
    [ -n "$1" ] && "$1" -I -c 'import sys; raise SystemExit(not (sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 11)))' >/dev/null 2>&1
}
py=
if [ -n "${PYJEV_PYTHON:-}" ]; then
    if ! valid311 "$PYJEV_PYTHON"; then
        echo "PYJEV_PYTHON must point to a working CPython 3.11 executable." >&2; exit 2
    fi
    py=$PYJEV_PYTHON
else
    for name in python3.11 python3; do
        if valid311 "$name"; then py=$name; break; fi
    done
    if [ -z "$py" ] && command -v pyenv >/dev/null 2>&1; then
        # pyenv's shim may exist even when it has no active 3.11 in this directory.
        installed=$(pyenv versions --bare | awk '/^3[.]11[.][0-9]+$/ {v=$0} END {print v}')
        if [ -n "$installed" ]; then
            path=$(pyenv prefix "$installed")/bin/python3.11
            if valid311 "$path"; then py=$path; fi
        fi
    fi
fi
if [ -z "$py" ]; then
    echo "CPython 3.11 was not found. Install it first or set PYJEV_PYTHON to its absolute path." >&2
    exit 2
fi
if [ "$mode" = runtime ]; then "$py" -I -m venv --without-pip "$dest"; else "$py" -I -m venv "$dest"; fi
"$dest/bin/python" -I -c 'import sys; print("CPython", sys.version.split()[0], "· isolated venv")'
