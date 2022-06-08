FROM registry.coombszy.com/discordbot-base:latest

# NOTE:
#   Packages and pip packages are installed via DockerfileBase image (discordbot-base)

WORKDIR /app

COPY start.sh start.sh
COPY bank bank
COPY chameleon chameleon
COPY store store
COPY gambling gambling
COPY polling polling
COPY requirements requirements
COPY lib lib
COPY emojis emojis
RUN mkdir config
COPY config/config.ini.sample config/config.ini
RUN mkdir data
RUN touch data/data.json data/data-bets.json data/data-polling.json

ARG bot
ENV bot ${bot}
CMD sh start.sh "${bot}"
