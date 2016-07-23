#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}")" && cd .. & pwd )"
mkdir -p "$DIR/instance"
if [ ! -f "$DIR/instance/oslobilder.db" ]; then
    echo "Creating instance/oslobilder.db from storage/baseline.sql"
    sqlite3 "$DIR/instance/oslobilder.db" < "$DIR/storage/baseline.sql"
else
    echo "instance/oslobilder.db already exists"
fi
