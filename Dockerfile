FROM python:3.8-slim-buster

WORKDIR /app

COPY start.sh start.sh
COPY bank bank
COPY chameleon chameleon
COPY requirements requirements
COPY lib lib
COPY config.ini.sample config.ini

RUN pip3 install -r requirements

ARG bot
ENV bot ${bot}
CMD sh start.sh "${bot}"