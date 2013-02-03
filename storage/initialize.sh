#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ ! -f "$DIR/oslobilder.db" ]; then
    echo "Creating oslobilder.db from baseline.sql"
    sqlite3 "$DIR/oslobilder.db" < "$DIR/baseline.sql"
else
    echo "oslobilder.db already exists"
fi
