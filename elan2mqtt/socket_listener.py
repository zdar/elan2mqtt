# -*- coding: utf-8 -*-

##########################################################################
#
# This is eLAN to MQTT gateway
#
# It operates in signle monolitic loop which peridically:
# - checks for websocket messages and processes them
#
# The JSON messages between the MQTT and eLAN are passed without processing
#  - status_topic: eLan/ADDR_OF_DEVICE/status
#  - control_topic: eLan/ADDR_OF_DEVICE/command
#
#
##########################################################################

import argparse
import aiohttp
import asyncio
import async_timeout

import paho.mqtt.client as mqtt

import json

import logging
import time

import hashlib

logger = logging.getLogger(__name__)

async def main():
    # placehloder for devices data
    d = {}
    u = {}
    async def publish_status(mac):
        """Publish message to status topic. Topic syntax is: elan / mac / status """
        if mac in d:
            logger.info("Getting and publishing status for " + d[mac]['url'])
            resp = await session.get(d[mac]['url'] + '/state', timeout=3)
            logger.debug(resp.status)
            if resp.status != 200:
                # There was problem getting status of device from eLan
                # This is usually caused by expiration of login
                # Let's try to relogin
                logger.warning(
                    "Getting status of device from eLan failed. Trying to relogin and get status.")
                await login(args.elan_user[0], str(args.elan_password[0]).encode('cp1250'))
                resp = await session.get(d[mac]['url'] + '/state', timeout=3)
            assert resp.status == 200, "Status retreival from eLan failed!"
            state = await resp.json()
            mqtt_cli.publish(d[mac]['status_topic'],
                            bytearray(json.dumps(state), 'utf-8'))
            logger.info(
                "Status published for " + d[mac]['url'] + " " + str(state))

    async def login(name, password):
        hash = hashlib.sha1(password).hexdigest()
        credentials = {
            'name': name,
            'key': hash
        }

        logger.info("Get main/login page (to get cookies)")
        # dirty check if we are authenticated and to get session
        resp = await session.get(args.elan_url + '/', timeout=3)

        logger.info("Are we already authenticated? E.g. API check")
        # dirty check if we are authenticated and to get session
        resp = await session.get(args.elan_url + '/api', timeout=3)

        not_logged = True

        while not_logged:
            if resp.status != 200:
                # perfrom login
                # it should result in new AuthID cookie
                logger.info("Authenticating to eLAN")
                resp = await session.post(args.elan_url + '/login', data=credentials)

        # Get list of devices
        # If we are not athenticated if will raise exception due to json
        # --> it triggers loop reset with new authenticatin attempt
            time.sleep(1)
            logger.info("Getting eLan device list")
            resp = await session.get(args.elan_url + '/api/devices', timeout=3)
            #print(resp.text)
            if resp.status == 200:
                not_logged = False

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.connected_flag = True
            logger.info("Connected to MQTT broker")
        else:
            logger.error("Bad connection Returned code = " + str(rc))

    def on_disconnect(client, userdata, rc):
        logging.info("MQTT broker disconnected. Reason: " + str(rc))
        mqtt_cli.connected_flag = False

    def on_message(client, userdata, message):
        global pending_message
        logging.info("MQTT broker message. " + str(message.topic))
        pending_message.append(message)
    
    
    # setup mqtt
    mqtt.Client.connected_flag = False
    mqtt_cli = mqtt.Client("eLan2MQTT_socket_listener" + args.mqtt_id)
    logger.info("Connecting to MQTT broker")
    logger.info(args.mqtt_broker)

    mqtt_broker = args.mqtt_broker
    i = mqtt_broker.find('mqtt://')
    if i < 0:
        raise Exception('MQTT URL not provided!')

    # Strip mqtt header from URL
    mqtt_broker = mqtt_broker[7:]

    i = mqtt_broker.find('@')
    mqtt_username = ""
    mqtt_password = ""

    # parse MQTT URL
    if (i > 0):
        # We have credentials
        mqtt_username = mqtt_broker[0:i]
        mqtt_broker = mqtt_broker[i+1:]
        i = mqtt_username.find(':')
        if (i > 0):
            # We have password
            mqtt_password = mqtt_username[i+1:]
            mqtt_username = mqtt_username[0:i]

    mqtt_cli.username_pw_set(username=mqtt_username, password=mqtt_password)
    # bind call back functions
    mqtt_cli.on_connect = on_connect
    mqtt_cli.on_disconnect = on_disconnect
    mqtt_cli.on_message = on_message
    mqtt_cli.connect(mqtt_broker, 1883, 120)
    mqtt_cli.loop_start()

    # Let's give MQTT some time to connect
    time.sleep(5)

    # wait for connection
    if not mqtt_cli.connected_flag:
        raise Exception('MQTT not connected!')

    logger.info("Connected to MQTT broker")

    # Connect to eLan and
    cookie_jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(cookie_jar=cookie_jar)
    # authentication to eLAN
    # from firmware v 3.0. the password is hashed
    # older firmwares work without authentication
    await login(args.elan_user[0], str(args.elan_password[0]).encode('cp1250'))

    # Get list of devices
    # If we are not athenticated it will raise exception due to json
    logger.info("Getting eLan device list")
    resp = await session.get(args.elan_url + '/api/devices', timeout=3)
    device_list = await resp.json()

    logger.info("Devices defined in eLan:\n" + str(device_list))

    for device in device_list:
        resp = await session.get(device_list[device]['url'], timeout=3)
        info = await resp.json()
        device_list[device]['info'] = info

        if "address" in info['device info']:
            mac = str(info['device info']['address'])
        else:
            mac = str(info['id'])
            logger.error("There is no MAC for device " + str(device_list[device]))
            device_list[device]['info']['device info']['address'] = mac

        u[device] = mac

        logger.info("Setting up " + device_list[device]['url'])
        #print("Setting up ", device_list[device]['url'], device_list[device])

        d[mac] = {
            'info': info,
            'url': device_list[device]['url'],
            'status_topic': ('eLan/' + mac + '/status'),
            'control_topic': ('eLan/' + mac + '/command')
        }


        #
        # topic syntax is: elan / mac / command | status
        #

        # We are not subsribed to any command topic

        # publish status over mqtt
        #print("Publishing status to topic " + d[mac]['status_topic'])
        await publish_status(mac)

    logger.info("Connecting to websocket to get updates")
    websocket = await session.ws_connect(args.elan_url + '/api/ws', timeout=1, autoping=True)
    logger.info("Socket connected")

    keep_alive_interval = 1 * 60  # interval between mandatory messages to keep connections open (and to renew session) in s (eLan session expires in 0.5 h)
    last_keep_alive = time.time()

    try:
        while True:  # Main loop
            # process status update announcement from eLan
            try:
                # every once so often do login
                if ((time.time() - last_keep_alive) > keep_alive_interval):
                    last_keep_alive = time.time()
                    #await login(args.elan_user[0], str(args.elan_password[0]).encode('cp1250'))
                    if mac is not None:
                        logger.info("Keep alive - status for MAC " + mac)
                        await publish_status(mac)
                # Waiting for WebSocket eLan message
                echo = await websocket.receive_json()
                if echo is None:
                    time.sleep(.25)
                    #print("Empty message?")
                else:
                    #print(echo)
                    id = echo["device"]
                    logger.info("Processing state change for " + u[id])
                    await publish_status(u[id])
            except:
                # It is perfectly normal to reach here - e.g. timeout
                time.sleep(.1)
                if not mqtt_cli.connected_flag:
                    raise ClientException("Broker not connected")
            time.sleep(.1)

        logger.error("Should not ever reach here")
        await c.disconnect()
    except ClientException as ce:
        logger.error("SOCKET LISTENER: Client exception: %s" % ce)
        try:
            await c.disconnect()
        except:
            pass
        time.sleep(5)


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        'elan_url', metavar='elan-url', help='URL of eLan (http://x.x.x.x/)')
    parser.add_argument(
        '-elan-user',
        metavar='elan_user',
        nargs=1,
        default='admin',
        dest='elan_user',
        help='username for eLan login')
    parser.add_argument(
        '-elan-password',
        metavar='elan_password',
        nargs=1,
        dest='elan_password',
        default='elkoep',
        help='password for eLan login')
    parser.add_argument(
        'mqtt_broker',
        metavar='mqtt-broker',
        help='MQTT broker (mqtt://user:password@x.x.x.x))')
    parser.add_argument(
        '-log-level',
        metavar='log_level',
        nargs=1,
        dest='log_level',
        default='warning',
        help='Log level debug|info|warning|error|fatal')
    parser.add_argument(
        '-mqtt-id',
        metavar='mqtt_id',
        nargs=1,
        dest='mqtt_id',
        default='',
        help='Client ID presented to MQTT server')

    args = parser.parse_args()

    formatter = "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    numeric_level = getattr(logging, args.log_level[0].upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = 30
    logging.basicConfig(level=numeric_level, format=formatter)

    # Loop foerver
    # Any error will trigger new startup
    while True:
        try:
            asyncio.get_event_loop().run_until_complete(main())
        except:
            logger.exception(
                "SOCKET LISTENER: Something went wrong. But don't worry we will start over again."
            )
            logger.error("But at first take some break. Sleeping for 5 s")
            time.sleep(5)
