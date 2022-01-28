ARG BUILD_FROM
FROM $BUILD_FROM

# Add env
ENV LANG C.UTF-8
ENV ELAN2MQTT_VERSION=1.15.0
ENV ARCHIVE=elan2mqtt-$ELAN2MQTT_VERSION

# Install requirements for add-on
RUN apk add --no-cache --update jq
#RUN apk add --no-cache --update python3 python3-dev py3-pip jq
RUN apk add --no-cache --update gcc g++ libc-dev python3-dev 
RUN mkdir /$ARCHIVE
RUN mkdir /$ARCHIVE/aiohttp

# Copy data for add-on
COPY run.sh /$ARCHIVE/run.sh
COPY main_worker.py /$ARCHIVE/main_worker.py
COPY socket_listener.py /$ARCHIVE/socket_listener.py
COPY aiohttp/* /$ARCHIVE/aiohttp/
COPY requirements.txt /$ARCHIVE/requirements.txt

# Let's set it to our add-on persistent data directory.
WORKDIR /$ARCHIVE

# install python packages
RUN pip install -r /$ARCHIVE/requirements.txt

RUN ["chmod", "a+x", "./run.sh"]

CMD [ "./run.sh" ]
