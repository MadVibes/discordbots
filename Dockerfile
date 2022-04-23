FROM python:3.8-slim-buster

# GCC is required but a python package
RUN apt-get update; apt-get install gcc ffmpeg libffi-dev apt-utils make g++ -y

WORKDIR /app

COPY start.sh start.sh
COPY bank bank
COPY chameleon chameleon
COPY shop shop
COPY gambling gambling
COPY polling polling
COPY requirements requirements
COPY lib lib
COPY config.ini config.ini

RUN pip3 install -r requirements

ARG bot
ENV bot ${bot}
CMD sh start.sh "${bot}"
