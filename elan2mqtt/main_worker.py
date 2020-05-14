# -*- coding: utf-8 -*-

##########################################################################
#
# This is eLAN to MQTT gateway
#
# It operates in signle monolitic loop which peridically:
# - checks for MQTT messages and processes them
# - periodically publishes status of all components
# - periodically publishes homeassistant discovery info
#
# The JSON messages between the MQTT and eLAN are passed without processing
#  - status_topic: eLan/ADDR_OF_DEVICE/status
#  - control_topic: eLan/ADDR_OF_DEVICE/command
#
# Discovery is published for:
# - lights (basic and dimmable)
# - termostats as temperature sensors
# Other devices can be directly defined in homeassistant YAML file
# or device discovery section needs to be extended
#
##########################################################################

import argparse
import aiohttp
import asyncio
import async_timeout

from hbmqtt.client import MQTTClient, ClientException

import json

import logging
import time

import hashlib

logger = logging.getLogger(__name__)

async def main():
    # placehloder for devices data
    d = {}
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
                logger.warning("Getting status of device from eLan failed. Trying to relogin and get status.")                
                await login(args.elan_user[0], str(args.elan_password[0]).encode('cp1250'))
                resp = await session.get(d[mac]['url'] + '/state', timeout=3)
            assert resp.status == 200, "Status retreival from eLan failed!"
            state = await resp.json()
            await c.publish(d[mac]['status_topic'],
                            bytearray(json.dumps(state), 'utf-8'))
            logger.info(
                "Status published for " + d[mac]['url'] + " " + str(state))

    async def publish_discovery(mac):
        """Publish message to status topic. Topic syntax is: elan / mac / status """
        if mac in d:
            if ("product type" in d[mac]['info']['device info']):
                # placeholder for device type versus protuct type check
                pass
            else:
                d[mac]['info']['device info']['product type'] = '---'
            logger.info("Publishing discovery for " + d[mac]['url'])
            ##########################################################################################
            # Device info library
            ##########################################################################################
            #
            ##########################################################################################
            # RFUS-61 - singel channel multi function relay
            ##########################################################################################
            # {"device info":{"type":"appliance","product type":"RFUS-61","address":123456,"label":"xxxx","vote":false},
            # 	"actions info": {
            # 		"on": {
            # 			"type": "bool"
            # 		},
            # 		"delayed off": {
            # 			"type": null
            # 		},
            # 		"delayed on": {
            # 			"type": null
            # 		},
            # 		"delayed off: set time": {
            # 			"type": "int",
            # 			"min": 2,
            # 			"max": 3600,
            # 			"step": 1
            # 		},
            # 		"delayed on: set time": {
            # 			"type": "int",
            # 			"min": 2,
            # 			"max": 3600,
            # 			"step": 1
            # 		},
            # 		"automat": {
            # 			"type": "bool"
            # 		} 
            # 	},
            # 	"primary actions": ["on"],
            # 	"secondary actions": [["delayed off", "delayed off: set time"], ["delayed on", "delayed on: set time"],"automat"],
            # 	"settings": {
            # 	"delayed off: set time": 2400,
            # 	"delayed on: set time": 2
            # 	},"id":"13212"}
            #
            # State:
            # {
            # 	"on": false,
            # 	"delay": false,
            # 	"automat": false,
            # 	"locked": false,
            # 	"delayed off: set time": 2400,
            # 	"delayed on: set time": 2
            # }

            ##########################################################################################
            # RFSA-66M - six channel multifunction relay (each channel is reported as separate device)
            ########################################################################################
            # {"id":"16619","device info":{"address":123456,"label":"xxxxx","type":"irrigation","product type":"RFSA-66M"},
            # 	"actions info": {
            # 		"on": {
            # 			"type": "bool"
            # 		},
            # 		"delayed off": {
            # 			"type": null
            # 		},
            # 		"delayed on": {
            # 			"type": null
            # 		},
            # 		"delayed off: set time": {
            # 			"type": "int",
            # 			"min": 2,
            # 			"max": 3600,
            # 			"step": 1
            # 		},
            # 		"delayed on: set time": {
            # 			"type": "int",
            # 			"min": 2,
            # 			"max": 3600,
            # 			"step": 1
            # 		},
            # 		"automat": {
            # 			"type": "bool"
            # 		} 
            # 	},
            # 	"primary actions": ["on"],
            # 	"secondary actions": [["delayed off", "delayed off: set time"], ["delayed on", "delayed on: set time"],"automat"],
            # 	"settings": {
            # 	"delayed off: set time": 1800,
            # 	"delayed on: set time": 0
            # 	}
            # }
            # State:
            # {
            # 	"on": false,
            # 	"delay": false,
            # 	"automat": false,
            # 	"locked": false,
            # 	"delayed off: set time": 1800,
            # 	"delayed on: set time": 0
            # }
            ##########################################################################################
            # RFSA-11B - single channel single function relay 
            ########################################################################################
            # {"id":"18457","device info":{"address":123456,"label":"abc","type":"appliance","product type":"RFSA-11B"},
            # 	"actions info": {
            # 		"on": {
            # 			"type": "bool"
            # 		},
            # 		"automat": {
            # 			"type": "bool"
            # 		} 
            # 	},
            # 	"primary actions": ["on"],
            # 	"secondary actions": ["automat"],
            # 	"settings": {}
            # }
            # State:
            # {
            # 	"on": true,
            # 	"automat": true,
            # 	"locked": false
            # }
            ##########################################################################################
            # RFSA-62B - dual channel multifunction relay 
            ########################################################################################
            # {
            # 	"id": "43124","device info":{"type":"appliance","product type":"RFSA-62B","address":123456,"label":"abc"},
            # 	"actions info": {
            # 		"on": {
            # 			"type": "bool"
            # 		},
            # 		"delayed off": {
            # 			"type": null
            # 		},
            # 		"delayed on": {
            # 			"type": null
            # 		},
            # 		"delayed off: set time": {
            # 			"type": "int",
            # 			"min": 2,
            # 			"max": 3600,
            # 			"step": 1
            # 		},
            # 		"delayed on: set time": {
            # 			"type": "int",
            # 			"min": 2,
            # 			"max": 3600,
            # 			"step": 1
            # 		},
            # 		"automat": {
            # 			"type": "bool"
            # 		} 
            # 	},
            # 	"primary actions": ["on"],
            # 	"secondary actions": [["delayed off", "delayed off: set time"], ["delayed on", "delayed on: set time"],"automat"],
            # 	"settings": {
            # 	"delayed off: set time": 15,
            # 	"delayed on: set time": 0
            # 	}
            # }
            # State:
            # {
            # 	"on": false,
            # 	"delay": false,
            # 	"automat": false,
            # 	"locked": false,
            # 	"delayed off: set time": 15,
            # 	"delayed on: set time": 0
            # }
            ##########################################################################################
            # RFSAI-61B - singel channel multi function relay with button
            ##########################################################################################
            # {
            # 	"id": "41008", "device info": {"type": "ventilation", "product type": "RFSAI-61B", "address": 123456, "label": "abc", "vote": false},
            # 	"actions info": {
            # 		"on": {
            # 			"type": "bool"
            # 		},
            # 		"delayed off": {
            # 			"type": null
            # 		},
            # 		"delayed on": {
            # 			"type": null
            # 		},
            # 		"delayed off: set time": {
            # 			"type": "int",
            # 			"min": 2,
            # 			"max": 3600,
            # 			"step": 1
            # 		},
            # 		"delayed on: set time": {
            # 			"type": "int",
            # 			"min": 2,
            # 			"max": 3600,
            # 			"step": 1
            # 		},
            # 		"automat": {
            # 			"type": "bool"
            # 		}
            # 	},
            # 	"primary actions": ["on"],
            # 	"secondary actions": [["delayed off", "delayed off: set time"], ["delayed on", "delayed on: set time"], "automat"],
            # 	"settings": {
            #             "delayed off: set time": 2,
            #             "delayed on: set time": 2
            # 	}
            # }
            # State:
            # {
            # 	"on": false,
            # 	"delay": false,
            # 	"automat": false,
            # 	"locked": false,
            # 	"delayed off: set time": 2,
            # 	"delayed on: set time": 2
            # }

            ##########################################################################################
            # RFSF-1B - flood detector
            ##########################################################################################
            # {"id":"55275","device info":{"address":239860,"label":"Voda","type":"flood detector","product type":"RFSF-1B"},
            # 	"actions info": {
            # 		"automat": {
            # 			"type": "bool"
            # 		},
            # 		"deactivate": {
            # 			"type": null
            # 		},
            # 		"disarm": {
            # 			"type": "bool"
            # 		} 
            # 	},
            # 	"primary actions": ["deactivate","disarm"],
            # 	"secondary actions": ["automat"],
            # 	"settings": {
            # 	"disarm": false
            # 	}
            # }
            # State:
            # {
            # 	"alarm": false,
            # 	"detect": false,
            # 	"automat": true,
            # 	"battery": true,
            # 	"disarm": false
            # }



            # User should set type to light. But sometimes...
            # That is why we will always treat RFDA-11B as a light dimmer
            #
            if ('light' in d[mac]['info']['device info']['type']) or ('lamp' in d[mac]['info']['device info']['type']) or (d[mac]['info']['device info']['product type'] == 'RFDA-11B'):
                logger.info(d[mac]['info']['device info'])

                if ('on' in d[mac]['info']['primary actions']):
                    logger.info("Primary action of light is ON")
                    discovery = {
                        'schema': 'basic',
                        'name': d[mac]['info']['device info']['label'],
                        'unique_id': ('eLan-' + mac),
                        'device': {
                            'name': d[mac]['info']['device info']['label'],
                            'identifiers' : ('eLan-light-' + mac),
                            'connections': [["mac",  mac]],
                            'mf': 'Elko EP',
                            'mdl': d[mac]['info']['device info']['product type']
                        },
                        'command_topic': d[mac]['control_topic'],
                        'state_topic': d[mac]['status_topic'],
                        'json_attributes_topic': d[mac]['status_topic'],
                        'payload_off': '{"on":false}',
                        'payload_on': '{"on":true}',
                        'state_value_template':
                        '{%- if value_json.on -%}{"on":true}{%- else -%}{"on":false}{%- endif -%}'
                    }
                    await c.publish('homeassistant/light/' + mac + '/config',
                                    bytearray(json.dumps(discovery), 'utf-8'))
                    logger.info("Discovery published for " + d[mac]['url'])
                    logger.debug(json.dumps(discovery))

                if ('brightness' in d[mac]['info']['primary actions']) or (d[mac]['info']['device info']['product type'] == 'RFDA-11B'):
                    logger.info("Primary action of light is BRIGHTNESS")
                    discovery = {
                        'schema': 'template',
                        'name': d[mac]['info']['device info']['label'],
                        'unique_id': ('eLan-' + mac),
                        'device': {
                            'name': d[mac]['info']['device info']['label'],
                            'identifiers' : ('eLan-dimmer-' + mac),
                            'connections': [["mac",  mac]],
                            'mf': 'Elko EP',
                            'mdl': d[mac]['info']['device info']['product type']
                        },
                        'state_topic': d[mac]['status_topic'],
                        #'json_attributes_topic': d[mac]['status_topic'],
                        'command_topic': d[mac]['control_topic'],
                        'command_on_template':
                        '{%- if brightness is defined -%} {"brightness": {{ (brightness * '
                        + str(d[mac]['info']['actions info']['brightness']
                              ['max']) +
                        ' / 255 ) | int }} } {%- else -%} {"brightness": 100 } {%- endif -%}',
                        'command_off_template': '{"brightness": 0 }',
                        'state_template':
                        '{%- if value_json.brightness > 0 -%}on{%- else -%}off{%- endif -%}',
                        'brightness_template':
                        '{{ (value_json.brightness * 255 / ' + str(
                            d[mac]['info']['actions info']['brightness']
                            ['max']) + ') | int }}'
                    }
                    await c.publish('homeassistant/light/' + mac + '/config',
                                    bytearray(json.dumps(discovery), 'utf-8'))
                    logger.info("Discovery published for " + d[mac]['url'])
                    logger.debug(json.dumps(discovery))

            #
            # Switches
            # RFSA-6xM units and "appliance" class of eLan
            # Note: handled as ELSE of light entities to avoid lights on RFSA-6xM units
            elif ('appliance' in d[mac]['info']['device info']['type']) or (d[mac]['info']['device info']['product type'] == 'RFSA-61M') or (d[mac]['info']['device info']['product type'] == 'RFSA-66M') or (d[mac]['info']['device info']['product type'] == 'RFSA-11B')  or (d[mac]['info']['device info']['product type'] == 'RFUS-61') or (d[mac]['info']['device info']['product type'] == 'RFSA-62B'):
                logger.info(d[mac]['info']['device info'])
                # "on" primary action is required for switches
                if ('on' in d[mac]['info']['primary actions']):
                    logger.info("Primary action of device is ON")
                    discovery = {
                        'schema': 'basic',
                        'name': d[mac]['info']['device info']['label'],
                        'unique_id': ('eLan-' + mac),
                        'device': {
                            'name': d[mac]['info']['device info']['label'],
                            'identifiers': ('eLan-switch-' + mac),
                            'connections': [["mac",  mac]],
                            'mf': 'Elko EP',
                            'mdl': d[mac]['info']['device info']['product type']
                        },
                        'command_topic': d[mac]['control_topic'],
                        'state_topic': d[mac]['status_topic'],
                        'json_attributes_topic': d[mac]['status_topic'],
                        'payload_off': '{"on":false}',
                        'payload_on': '{"on":true}',
                        'state_off': 'off',
                        'state_on' : 'on',
                        'value_template':
                        '{%- if value_json.on -%}on{%- else -%}off{%- endif -%}'
                    }
                    await c.publish('homeassistant/switch/' + mac + '/config',
                                    bytearray(json.dumps(discovery), 'utf-8'))
                    logger.info("Discovery published for " + d[mac]['url'])
                    logger.debug(json.dumps(discovery))


            #
            # Thermostats
            #
            # User should set type to heating. But sometimes...
            # That is why we will always treat RFSTI-11G a temperature sensor/thermostat
            #
            if (d[mac]['info']['device info']['type'] == 'heating') or (d[mac]['info']['device info']['product type'] == 'RFSTI-11G'):
                logger.info(d[mac]['info']['device info'])

                discovery = {
                    'name': d[mac]['info']['device info']['label'] + '-IN',
                    'unique_id': ('eLan-' + mac + '-IN'),
                    'device': {
                        'name': d[mac]['info']['device info']['label'],
                        'identifiers' : ('eLan-thermostat-' + mac),
                        'connections': [["mac",  mac]],
                        'mf': 'Elko EP',
                        'mdl': d[mac]['info']['device info']['product type']
                    },
                    'device_class': 'temperature',
                    'state_topic': d[mac]['status_topic'],
                    'json_attributes_topic': d[mac]['status_topic'],
                    'value_template': '{{ value_json["temperature IN"] }}',
                    'unit_of_measurement': '°C'
                }
                await c.publish('homeassistant/sensor/' + mac + '/IN/config',
                                bytearray(json.dumps(discovery), 'utf-8'))
                logger.info("Discovery published for " + d[mac]['url'])
                logger.debug(json.dumps(discovery))

                discovery = {
                    'name': d[mac]['info']['device info']['label'] + '-OUT',
                    'unique_id': ('eLan-' + mac + '-OUT'),
                    'device': {
                        'name': d[mac]['info']['device info']['label'],
                        'identifiers' : ('eLan-thermostat-' + mac),
                        'connections': [["mac",  mac]],
                        'mf': 'Elko EP',
                        'mdl': d[mac]['info']['device info']['product type']
                    },
                    'state_topic': d[mac]['status_topic'],
                    'json_attributes_topic': d[mac]['status_topic'],
                    'device_class': 'temperature',
                    'value_template': '{{ value_json["temperature OUT"] }}',
                    'unit_of_measurement': '°C'
                }
                await c.publish('homeassistant/sensor/' + mac + '/OUT/config',
                                bytearray(json.dumps(discovery), 'utf-8'))

                logger.info("Discovery published for " + d[mac]['url'])
                logger.debug(json.dumps(discovery))
#
# Note - needs to be converted to CLIMATE class
#
                discovery = {
                    'name': d[mac]['info']['device info']['label'] + '-ON',
                    'unique_id': ('eLan-' + mac + '-ON'),
                    'device': {
                        'name': d[mac]['info']['device info']['label'],
                        'identifiers' : ('eLan-thermostat-' + mac),
                        'connections': [["mac",  mac]],
                        'mf': 'Elko EP',
                        'mdl': d[mac]['info']['device info']['product type']
                    },
                    'state_topic': d[mac]['status_topic'],
                    'json_attributes_topic': d[mac]['status_topic'],
#                    'device_class': 'heat',
                    'value_template':
                    '{%- if value_json.on -%}on{%- else -%}off{%- endif -%}'
#                    'command_topic': d[mac]['control_topic']
                }
                await c.publish('homeassistant/sensor/' + mac + '/ON/config',
                                bytearray(json.dumps(discovery), 'utf-8'))

                logger.info("Discovery published for " + d[mac]['url'])
                logger.debug(json.dumps(discovery))
            #
            # Thermometers
            #
            # User should set type to thermometer. But sometimes...
            #

            if (d[mac]['info']['device info']['type'] == 'thermometer') or (d[mac]['info']['device info']['product type'] == 'RFTI-10B'):
                logger.info(d[mac]['info']['device info'])

                discovery = {
                    'name': d[mac]['info']['device info']['label'] + '-IN',
                    'unique_id': ('eLan-' + mac + '-IN'),
                    'device': {
                        'name': d[mac]['info']['device info']['label'],
                        'identifiers': ('eLan-thermometer-' + mac),
                        'connections': [["mac",  mac]],
                        'mf': 'Elko EP',
                        'mdl': d[mac]['info']['device info']['product type']
                    },
                    'device_class': 'temperature',
                    'state_topic': d[mac]['status_topic'],
                    'json_attributes_topic': d[mac]['status_topic'],
                    'value_template': '{{ value_json["temperature IN"] }}',
                    'unit_of_measurement': '°C'
                }
                await c.publish('homeassistant/sensor/' + mac + '/IN/config',
                                bytearray(json.dumps(discovery), 'utf-8'))
                logger.info("Discovery published for " + d[mac]['url'])
                logger.debug(json.dumps(discovery))

                discovery = {
                    'name': d[mac]['info']['device info']['label'] + '-OUT',
                    'unique_id': ('eLan-' + mac + '-OUT'),
                    'device': {
                        'name': d[mac]['info']['device info']['label'],
                        'identifiers': ('eLan-thermometer-' + mac),
                        'connections': [["mac",  mac]],
                        'mf': 'Elko EP',
                        'mdl': d[mac]['info']['device info']['product type']
                    },
                    'state_topic': d[mac]['status_topic'],
                    'json_attributes_topic': d[mac]['status_topic'],
                    'device_class': 'temperature',
                    'value_template': '{{ value_json["temperature OUT"] }}',
                    'unit_of_measurement': '°C'
                }
                await c.publish('homeassistant/sensor/' + mac + '/OUT/config',
                                bytearray(json.dumps(discovery), 'utf-8'))

                logger.info("Discovery published for " + d[mac]['url'])
                logger.debug(json.dumps(discovery))



            #
            # Detectors
            #
            # RFWD-100 status messages
            # {alarm: true, detect: false, tamper: “closed”, automat: false, battery: true, disarm: false}
            # {alarm: true, detect: true, tamper: “closed”, automat: false, battery: true, disarm: false}
            # RFSF-1B status message
            # {"alarm": false,	"detect": false, "automat": true, "battery": true, "disarm": false }

            if ('detector' in d[mac]['info']['device info']['type']) or ('RFWD-' in d[mac]['info']['device info']['product type']) or ('RFSD-' in d[mac]['info']['device info']['product type']) or ('RFMD-' in d[mac]['info']['device info']['product type']) or ('RFSF-' in d[mac]['info']['device info']['product type']):
                logger.info(d[mac]['info']['device info'])

                icon = ''

                # A wild guess of icon
                if ('window' in d[mac]['info']['device info']['type']) or ('RFWD-' in d[mac]['info']['device info']['product type']):
                    icon = 'mdi:window-open'
                    if ('door' in str(d[mac]['info']['device info']['label']).lower()):
                        icon = 'mdi:door-open'

                if ('smoke' in d[mac]['info']['device info']['type']) or ('RFSD-' in d[mac]['info']['device info']['product type']):
                    icon = 'mdi:smoke-detector'

                if ('motion' in d[mac]['info']['device info']['type']) or ('RFMD-' in d[mac]['info']['device info']['product type']):
                    icon = 'mdi:motion-sensor'

                if ('flood' in d[mac]['info']['device info']['type']) or ('RFSF-' in d[mac]['info']['device info']['product type']):
                    icon = 'mdi:waves'


                # Silently expect that all detectors provide "detect" action
                discovery = {
                    'name': d[mac]['info']['device info']['label'],
                    'unique_id': ('eLan-' + mac),
                    'device': {
                        'name': d[mac]['info']['device info']['label'],
                        'identifiers' : ('eLan-detector-' + mac),
                        'connections': [["mac",  mac]],
                        'mf': 'Elko EP',
                        'mdl': d[mac]['info']['device info']['product type']
                    },
                    'state_topic': d[mac]['status_topic'],
                    'json_attributes_topic': d[mac]['status_topic'],
#                    'device_class': 'heat',
                    'value_template':
                    '{%- if value_json.detect -%}on{%- else -%}off{%- endif -%}'
#                    'command_topic': d[mac]['control_topic']
                }

                if (icon != ''):
                    discovery['icon'] = icon

                await c.publish('homeassistant/sensor/' + mac + '/config',
                                bytearray(json.dumps(discovery), 'utf-8'))

                logger.info("Discovery published for " + d[mac]['url'])
                logger.debug(json.dumps(discovery))

                # Silently expect that all detectors provide "battery" status
                # Battery
                discovery = {
                    'name': d[mac]['info']['device info']['label'] + 'battery',
                    'unique_id': ('eLan-' + mac + '-battery'),
                    'device': {
                        'name': d[mac]['info']['device info']['label'],
                        'identifiers' : ('eLan-detector-' + mac),
                        'connections': [["mac",  mac]],
                        'mf': 'Elko EP',
                        'mdl': d[mac]['info']['device info']['product type']
                    },
                    'device_class': 'battery',
                    'state_topic': d[mac]['status_topic'],
                    #'json_attributes_topic': d[mac]['status_topic'],
                    'value_template':
                    '{%- if value_json.battery -%}100{%- else -%}0{%- endif -%}'
#                    'command_topic': d[mac]['control_topic']
                }
                await c.publish('homeassistant/sensor/' + mac + '/battery/config',
                                bytearray(json.dumps(discovery), 'utf-8'))

                logger.info("Discovery published for " + d[mac]['url'])
                logger.debug(json.dumps(discovery))


                # START - RFWD window/door detector
                if (d[mac]['info']['device info']['product type'] == 'RFWD-100') or (d[mac]['info']['device info']['product type'] == 'RFSF-1B'):
                    # RFWD-100 status messages
                    # {alarm: true, detect: false, tamper: “closed”, automat: false, battery: true, disarm: false}
                    # {alarm: true, detect: true, tamper: “closed”, automat: false, battery: true, disarm: false}
                    # RFSF-1B
                    # {"alarm": false,	"detect": false, "automat": true, "battery": true, "disarm": false }
                    # Alarm
                    discovery = {
                        'name': d[mac]['info']['device info']['label'] + 'alarm',
                        'unique_id': ('eLan-' + mac + '-alarm'),
                        'icon': 'mdi:alarm-light',
                        'device': {
                            'name': d[mac]['info']['device info']['label'],
                            'identifiers' : ('eLan-detector-' + mac),
                            'connections': [["mac",  mac]],
                            'mf': 'Elko EP',
                            'mdl': d[mac]['info']['device info']['product type']
                        },
                        'state_topic': d[mac]['status_topic'],
                        'json_attributes_topic': d[mac]['status_topic'],
                        'value_template':
                        '{%- if value_json.alarm -%}on{%- else -%}off{%- endif -%}'
    #                    'command_topic': d[mac]['control_topic']
                    }
                    await c.publish('homeassistant/sensor/' + mac + '/alarm/config',
                                    bytearray(json.dumps(discovery), 'utf-8'))

                    logger.info("Discovery published for " + d[mac]['url'])
                    logger.debug(json.dumps(discovery))

                if (d[mac]['info']['device info']['product type'] == 'RFWD-100'):
                    # Tamper
                    # RFWD-100 status messages
                    # {alarm: true, detect: false, tamper: “closed”, automat: false, battery: true, disarm: false}
                    # {alarm: true, detect: true, tamper: “closed”, automat: false, battery: true, disarm: false}
                    discovery = {
                        'name': d[mac]['info']['device info']['label'] + 'tamper',
                        'unique_id': ('eLan-' + mac + '-tamper'),
                        'icon': 'mdi:gesture-tap',
                        'device': {
                            'name': d[mac]['info']['device info']['label'],
                            'identifiers' : ('eLan-detector-' + mac),
                            'connections': [["mac",  mac]],
                            'mf': 'Elko EP',
                            'mdl': d[mac]['info']['device info']['product type']
                        },
                        'state_topic': d[mac]['status_topic'],
                        'json_attributes_topic': d[mac]['status_topic'],
                        'value_template':
                        '{%- if value_json.tamper == "opened" -%}on{%- else -%}off{%- endif -%}'
    #                    'command_topic': d[mac]['control_topic']
                    }
                    await c.publish('homeassistant/sensor/' + mac + '/tamper/config',
                                    bytearray(json.dumps(discovery), 'utf-8'))

                    logger.info("Discovery published for " + d[mac]['url'])
                    logger.debug(json.dumps(discovery))

                    # Automat
                    discovery = {
                        'name': d[mac]['info']['device info']['label'] + 'automat',
                        'unique_id': ('eLan-' + mac + '-automat'),
                        'icon': 'mdi:arrow-decision-auto',
                        'device': {
                            'name': d[mac]['info']['device info']['label'],
                            'identifiers' : ('eLan-detector-' + mac),
                            'connections': [["mac",  mac]],
                            'mf': 'Elko EP',
                            'mdl': d[mac]['info']['device info']['product type']
                        },
                        'state_topic': d[mac]['status_topic'],
                        'json_attributes_topic': d[mac]['status_topic'],
                        'value_template':
                        '{%- if value_json.automat -%}on{%- else -%}off{%- endif -%}'
    #                    'command_topic': d[mac]['control_topic']
                    }
                    await c.publish('homeassistant/sensor/' + mac + '/automat/config',
                                    bytearray(json.dumps(discovery), 'utf-8'))

                    logger.info("Discovery published for " + d[mac]['url'])
                    logger.debug(json.dumps(discovery))

                    # Disarm
                    discovery = {
                        'name': d[mac]['info']['device info']['label'] + 'disarm',
                        'unique_id': ('eLan-' + mac + '-disarm'),
                        'icon': 'mdi:lock-alert',
                        'device': {
                            'name': d[mac]['info']['device info']['label'],
                            'identifiers' : ('eLan-detector-' + mac),
                            'connections': [["mac",  mac]],
                            'mf': 'Elko EP',
                            'mdl': d[mac]['info']['device info']['product type']
                        },
                        'state_topic': d[mac]['status_topic'],
                        'json_attributes_topic': d[mac]['status_topic'],
                        'value_template':
                        '{%- if value_json.disarm -%}on{%- else -%}off{%- endif -%}'
    #                    'command_topic': d[mac]['control_topic']
                    }
                    await c.publish('homeassistant/sensor/' + mac + '/disarm/config',
                                    bytearray(json.dumps(discovery), 'utf-8'))

                    logger.info("Discovery published for " + d[mac]['url'])
                    logger.debug(json.dumps(discovery))

                # END - RFWD window/door detector




    async def on_message(topic, data):
        #print("Got message:", topic, data)
        try:
            tmp = topic.split('/')
            # check if it is one of devices we know
            if (tmp[0] == 'eLan') and (tmp[2] == 'command') and (tmp[1] in d):
                #post command to device - warning there are no checks
                #print(d[tmp[1]]['url'], data)
                data = json.loads(data)
                resp = await session.put(d[tmp[1]]['url'], json=data)
                #print(resp)
                info = await resp.text()
                #print(info)
                # check and publish updated state of device
                await publish_status(tmp[1])
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])

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
                resp = await session.post(args.elan_url + '/login',data=credentials)


        # Get list of devices
        # If we are not athenticated if will raise exception due to json
        # --> it triggers loop reset with new authenticatin attempt
            logger.info("Getting eLan device list")
            resp = await session.get(args.elan_url + '/api/devices', timeout=3)
            #print(resp.text)
            if  resp.status == 200:
                not_logged = False


    # setup mqtt (aiomqtt)
    c = MQTTClient(config={'auto_reconnect': False})
    logger.info("Connecting to MQTT broker")
    logger.info(args.mqtt_broker)
    await c.connect(args.mqtt_broker)
    logger.info("Connected to MQTT broker")

    # Connect to eLan and
    cookie_jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(cookie_jar=cookie_jar)
    # authentication to eLAN
    # from firmware v 3.0. the password is hashed
    # older firmwares work without authentication
    await login(args.elan_user[0],str(args.elan_password[0]).encode('cp1250'))

    # Get list of devices
    # If we are not athenticated if will raise exception due to json
    # --> it triggers loop reset with new authenticatin attempt
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

        # subscribe to control topic
        logger.info("Subscribing to control topic " + d[mac]['control_topic'])
        await c.subscribe([(d[mac]['control_topic'], 1)])
        logger.info("Subscribed to " + d[mac]['control_topic'])

        # publish autodiscovery info
        #logger.info("Autodiscovery disabled: " + str(args.disable_autodiscovery))

        if args.disable_autodiscovery==True:
            logger.info("Autodiscovery disabled")
        else:
            await publish_discovery(mac)

        # publish status over mqtt
        #print("Publishing status to topic " + d[mac]['status_topic'])
        await publish_status(mac)

    pass

    i = 0
    try:
        login_interval = 6 * 60 * 60  # interval between logins (to renew session) in s
        discovery_interval = 10 * 60  # interval between autodiscovery messages in s
        info_interval = 1 * 60  # interval between periodic status messages
        last_login = time.time()
        last_discovery = time.time()
        last_info = time.time()
        while True:  # Main loop
            # every once so often do login
            if ((time.time() - last_login) > login_interval):
                last_login = time.time()
                await login(args.elan_user[0],str(args.elan_password[0]).encode('cp1250'))

            # every once so often publish status (just for sure)
            if ((time.time() - last_info) > info_interval):
                try:
                    last_info = time.time()
                    # publish discovery info
                    if ((time.time() - last_discovery) > discovery_interval):
                        last_discovery = time.time()
                        for device in device_list:
                            mac = str(device_list[device]['info'][
                                'device info']['address'])
                            if args.disable_autodiscovery==True:
                                logger.info("Autodiscovery disabled")
                            else:
                                await publish_discovery(mac)

                    for device in device_list:
                        mac = str(device_list[device]['info']['device info'][
                            'address'])
                        await publish_status(mac)

                except asyncio.TimeoutError:
                    # TimeoutError exception during status or discovery
                    pass
                    time.sleep(0.1)
            # process incomming MQTT commands
            try:
                # Waiting for MQTT message
                message = await c.deliver_message(timeout=0.5)
                packet = message.publish_packet
                i = i + 1
                #print("Processing MQTT message %d:  %s => %s" %
                #      (i, packet.variable_header.topic_name,
                #       str(packet.payload.data)))
                await on_message(packet.variable_header.topic_name,
                                 packet.payload.data.decode("utf-8"))
            except asyncio.TimeoutError:
                # It is perfectly normal to reach here - e.g. timeout
                pass
                time.sleep(0.2)


        logger.error("MAIN WORKER: Should not ever reach here")
        await c.disconnect()
    except ClientException as ce:
        logger.error("MAIN WORKER: Client exception: %s" % ce)
        try:
            await c.disconnect()
        except:
            pass
        time.sleep(5)


def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(description='Process some arguments.')
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
        '-disable-autodiscovery',
        metavar='disable_autodiscovery',
        nargs='?',
        dest='disable_autodiscovery',
        default=False,
        type=str2bool,
        help='Disable autodiscovery True|False')
       
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
                "MAIN WORKER: Something went wrong. But don't worry we will start over again."
            )
            logger.error("But at first take some break. Sleeping for 10 s")
            time.sleep(10)
