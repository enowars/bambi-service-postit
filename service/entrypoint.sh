#!/bin/bash

chown -R service:service /service /data

expiry=$((13*60))
while [ 1 ]; do
	reftime="$(($(date +%s)-$expiry))"
	echo "[FILE CLEANUP] @ $(date +%T)"
	/service/cleandb "/data/db.sqlite3" "$reftime" &> /tmp/cleaner-log
	sleep 70
done &

CMD="ncat --keep-open --listen -p 9000 --max-conns 4000 \
--no-shutdown --wait 10s --sh-exec '/service/postit /data/db.sqlite3'"
su -s /bin/sh -c "$CMD" service
