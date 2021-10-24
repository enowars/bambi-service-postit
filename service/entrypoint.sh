#!/bin/bash

chown -R service:service /service /data

while [ 1 ]; do
	echo "[DB CLEANUP] @ $(date +%T)"
	/service/cleandb "/data/db.sqlite3" 2>&1 | tee /tmp/cleaner-log
	sleep 60
done &

CMD="ncat --keep-open --listen -p 9000 --max-conns 4000 \
--no-shutdown --wait 10s --sh-exec '/service/postit /data/db.sqlite3'"
su -s /bin/sh -c "$CMD" service
