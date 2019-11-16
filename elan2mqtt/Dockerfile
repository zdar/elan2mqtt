ARG BUILD_FROM
FROM $BUILD_FROM

# Add env
ENV LANG C.UTF-8
ENV ELAN2MQTT_VERSION=1.1.0
ENV ARCHIVE=elan2mqtt-$ELAN2MQTT_VERSION

# Install requirements for add-on
RUN apk add --no-cache --update python3 jq
RUN mkdir /$ARCHIVE
RUN mkdir /$ARCHIVE/aiohttp

# Copy data for add-on
COPY run.sh /$ARCHIVE/run.sh
COPY main.py /$ARCHIVE/main.py
COPY aiohttp/* /$ARCHIVE/aiohttp/
COPY requirements.txt /$ARCHIVE/requirements.txt

# Let's set it to our add-on persistent data directory.
WORKDIR /$ARCHIVE

RUN ["chmod", "a+x", "./run.sh"]

CMD [ "./run.sh" ]
