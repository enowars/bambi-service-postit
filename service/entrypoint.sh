#!/bin/bash

chown -R service:service /service /data

runas() {
    su -s /bin/sh -c "$2" "$1"
}

if [ ! -e "/data/db.sqlite3" ]; then
    runas service "/service/gendb /data/db.sqlite3"
fi

while [ 1 ]; do
	echo "[DB CLEANUP] @ $(date +%T)"
	runas service "/service/cleandb /data/db.sqlite3"
	sleep 60
done &

runas service "ncat --keep-open --listen -p 9000 --no-shutdown\
    --wait 10s --sh-exec '/service/postit /data/db.sqlite3'"
