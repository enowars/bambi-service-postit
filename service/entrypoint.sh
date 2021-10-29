#!/bin/bash

if [ ! -e "/service/data/db.sqlite3" ]; then
    /service/gendb /service/data/db.sqlite3
fi

while [ 1 ]; do
	echo "[DB CLEANUP] @ $(date +%T)"
	/service/cleandb /service/data/db.sqlite3
	sleep 60
done &

ncat --keep-open --listen -p 9000 --no-shutdown \
    --wait 10s --sh-exec '/service/postit /service/data/db.sqlite3'
