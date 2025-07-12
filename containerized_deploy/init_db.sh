#!/bin/bash

set -eo pipefail
shopt -s nullglob

init_db() {
    echo "Importing data for crk_oahpa..."
    gzip -dc /tmp/crk_oahpa_sqlite.sql.gz | sqlite3 /app/crk_oahpa_project/crk_oahpa.sqlite3
}

init_db
echo "database created. commit image layer takes a few seconds..."

# when using both ENTRYPOINT and CMD in a Dockerfile, the CMD is treated
# as argument to the ENTRYPOINT... so exec the real CMD to run it
#exec "$@"
