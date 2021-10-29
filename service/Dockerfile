FROM ubuntu:18.04

RUN useradd -ms /bin/bash -u 1000 service

RUN apt update && apt install -y --no-install-recommends \
	nmap gcc make libc6-dev libc6 libc-dev-bin libsqlite3-dev libgmp-dev

COPY entrypoint.sh /
RUN chmod 755 /entrypoint.sh

COPY src/ /service
RUN make -C /service clean && make -C /service
RUN chmod +x /service/postit /service/cleandb /service/gendb
RUN chown -R service:service /service
WORKDIR /service

EXPOSE 9000

ENTRYPOINT ["sh", "-c", "chmod -R 777 /service && su -c /entrypoint.sh service"]
