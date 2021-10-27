FROM python:3.9-buster

RUN useradd -ms /bin/bash -u 1000 checker

ENV TERM=linux
ENV TERMINFO=/etc/terminfo

RUN apt update && DEBIAN_FRONTEND=noninteractive apt-get install libmpfr-dev libmpc-dev

COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

COPY ./src /checker
WORKDIR /checker
RUN chown checker -R /checker

USER checker
RUN python3 -m pip install --no-warn-script-location -r requirements.txt

ENTRYPOINT [ "/entrypoint.sh" ]
