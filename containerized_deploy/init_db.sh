#!/bin/bash

set -eo pipefail
shopt -s nullglob

start_db() {
    echo "Starting mariadbd temporarily..."
    /usr/sbin/mariadbd --user=root --socket=/run/mysqld/mysqld.sock &
    MARIADB_PID=$!

    echo "Waiting for mariadb to be ready to accept connections..."
    for i in {10..0}; do
        if (echo SELECT 1 | mariadb >/dev/null 2>&1); then
            break
        fi
        sleep 1
    done

    if [ "$i" = 0 ]; then
        echo "Unable to start mariadbd, aborting"
        exit 1
    fi
}

stop_db() {
    echo "Stopping mariadbd..."
    kill "$MARIADB_PID"
    wait "$MARIADB_PID"
}

init_db() {
    echo "Creating database crk_oahpa..."
    echo "CREATE DATABASE crk_oahpa" | mariadb
    echo "Creating crk_oahpa user..."
    echo "CREATE USER 'crk_oahpa'@'%' IDENTIFIED BY 'crkGOGOcrk' PASSWORD EXPIRE NEVER;" | mariadb
    echo "GRANT ALL PRIVILEGES ON *.* TO 'crk_oahpa'@'%' IDENTIFIED BY 'crkGOGOcrk';" | mariadb
    echo "Importing data for crk_oahpa..."
    gzip -dc /tmp/crk_oahpa.sql.gz | mariadb --password=crkGOGOcrk --user=crk_oahpa crk_oahpa
}

start_db
init_db
stop_db
echo "database created. commit image layer takes a few seconds..."

# when using both ENTRYPOINT and CMD in a Dockerfile, the CMD is treated
# as argument to the ENTRYPOINT... so exec the real CMD to run it
#exec "$@"
