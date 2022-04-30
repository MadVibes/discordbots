FROM registry.coombszy.com/discordbot-base:latest

WORKDIR /app

COPY start.sh start.sh
COPY bank bank
COPY chameleon chameleon
COPY shop shop
COPY gambling gambling
COPY polling polling
COPY requirements requirements
COPY lib lib
RUN mkdir config
COPY config/config.ini.sample config/config.ini
RUN mkdir data
RUN touch data/data.json data/data-bets.json data/data-polling.json

RUN pip3 install -r requirements

ARG bot
ENV bot ${bot}
CMD sh start.sh "${bot}"
