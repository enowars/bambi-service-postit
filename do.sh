#!/bin/sh

shopt -s expand_aliases
alias pushd="pushd &>/dev/null"
alias popd="popd &>/dev/null"

if [ "$1" == "ci-test" ]; then
	if [ "$2" == "run" ]; then
		sudo docker-compose -f checker/docker-compose.yml up --build -d -V
		sudo docker-compose -f service/docker-compose.yml up --build -d -V
	fi

	if [ -z "$CHECKER_ADDRESS" -o -z "$SERVICE_ADDRESS" ]; then
		echo "Specify addresses via SERVICE_ADDRESS / CHECKER_ADDRESS vars"
		exit 1
	fi
	export ENOCHECKER_TEST_CHECKER_ADDRESS=$CHECKER_ADDRESS
	export ENOCHECKER_TEST_CHECKER_PORT=$CHECKER_PORT
	export ENOCHECKER_TEST_SERVICE_ADDRESS=$SERVICE_ADDRESS
	export ENOCHECKER_TEST_SERVICE_PORT=$SERVICE_PORT
	enochecker_test

	sudo docker-compose -f service/docker-compose.yml logs --no-color --tail=1000 > /tmp/ci-test-service.log
	sudo docker-compose -f checker/docker-compose.yml logs --no-color --tail=1000 > /tmp/ci-test-checker.log

	if [ "$2" == "run" ]; then
		sudo docker-compose -f service/docker-compose.yml down
		sudo docker-compose -f checker/docker-compose.yml down
	fi
elif [ "$1" == "checker-local" ]; then
	cd checker
	if [ -z "$(sudo docker ps | grep postit-mongo)" ]; then
		sudo docker-compose down -v
		sudo docker-compose up -d postit-mongo
	fi

	export MONGO_ENABLED=1
	export MONGO_HOST=localhost
	export MONGO_PORT=27017
	export MONGO_USER=postit_mongo
	export MONGO_PASSWORD=postit_mongo

	cd src
	gunicorn -c gunicorn.conf.py checker:app
elif [ "$1" == "parse-log" ]; then
	python3 -c '
#!/usr/bin/env python3

import jsons, sys

for l in open(sys.argv[1]).read().split("\n"):
	if "##ENOLOGMESSAGE" not in l: continue
	l = l.split("##ENOLOGMESSAGE ", 1)[1]
	jmsg = jsons.loads(l)
	print("[[ %s #%s ]] " % (jmsg["method"], jmsg["variantId"]), end="")
	print(jmsg["message"] + "\n--------")
	' "$2"
fi
