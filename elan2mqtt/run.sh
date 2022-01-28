#!/bin/bash

echo "Run.sh starting"
CONFIG_PATH=/data/options.json
SYSTEM_USER=/data/system_user.json

ELAN_URL=$(jq --raw-output ".eLanURL" $CONFIG_PATH)
MQTT_SERVER=$(jq --raw-output ".MQTTserver" $CONFIG_PATH)
USERNAME=$(jq --raw-output ".username" $CONFIG_PATH)
PASSWORD=$(jq --raw-output ".password" $CONFIG_PATH)
LOGLEVEL=$(jq --raw-output ".log_level" $CONFIG_PATH)
DISABLEAUTODISCOVERY=$(jq --raw-output ".disable_autodiscovery" $CONFIG_PATH)

#echo "Installing requirements"
#pip3 install -r requirements.txt

echo "Starting gateway"
echo ${ELAN_URL} ${MQTT_SERVER}
echo "Loglevel:" ${LOGLEVEL} 
echo "Autodiscovery disabled:" ${DISABLEAUTODISCOVERY}
python3 main_worker.py ${ELAN_URL} ${MQTT_SERVER} -elan-user ${USERNAME} -elan-password ${PASSWORD} -log-level ${LOGLEVEL} -disable-autodiscovery ${DISABLEAUTODISCOVERY} & python3 socket_listener.py ${ELAN_URL} ${MQTT_SERVER} -elan-user ${USERNAME} -elan-password ${PASSWORD} -log-level ${LOGLEVEL} 
