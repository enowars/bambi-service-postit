FROM ubuntu:18.04

RUN apt update && apt install -y --no-install-recommends \
	nmap gcc make libc6-dev libc6 libc-dev-bin libsqlite3-dev libgmp-dev

RUN addgroup --system service
RUN adduser --system --ingroup service --uid 1000 service

COPY entrypoint.sh /
RUN chmod 755 /entrypoint.sh

COPY src/ /service
RUN make -C /service clean && make -C /service
RUN chmod +x /service/postit /service/cleandb /service/gendb
WORKDIR /service/

EXPOSE 9000

ENTRYPOINT ["/entrypoint.sh"]
