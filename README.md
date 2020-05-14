# elan2mqtt
MQTT gateway for ElkoEP iNELS RF system https://www.elkoep.com/wireless-rf-control

Can be used as:
- Hass.io add-on
- Standalone eLan (iNELS RF) to MQTT gateway

Works with Home Assistant (supports autodiscovery) and other MQTT compatible home automation systems (OpenHAB,...)

# Requirements
- eLan RF Gateway https://www.elkoep.com/smart-rf-box-elan-rf-003
- python

Note: all connected devices must be defined on eLan

# Hass.IO (Home Assistant)
- Manual - Copy elan2mqtt directory into Hass addons directory
- Automatic - Add https://github.com/zdar/elan2mqtt as a new repository and install


# Standalone
Use python to run main_worker.py and socket_listener.py (check command line arguments)

# Device not supported by autodiscovery
Elan2mqtt has only limited autodiscovery for Home Assistant. If the device is not discovered by Home Assistant it can still be used. All devices can be manually defined using MQTT integration. For each device two topics are created:
- **Status** messages are using topic /eLan/*device_mac_address*/status
- **Command** messages are using topic /eLan/*device_mac_address*/command

# Getting support for autodiscovery of your device
To get you device supported please open Issue ticket in github.
In ticket you have to provide:
- device type (product name)
- device type as selected in eLan (light, heating,...)
- device info message*
- device status message*
- example of device commands*
and when possible home assistant MQTT definition

_(*) these can be captured using google web browser. Open developer tools (F12), log in into elan, use your device. In network tab you will see messages passing between browser and elan. Attach those relevant to you device._

# Currently tested devices
Device | eLan type | Home Assitant
---|---|---
RFSA-66M | light | MQTT template light
RFDA-11B | dimmed light | MQTT template dimmer light
RFSTI-11G | heating | MQTT template sensors: 2x temperature (-IN,-OUT), heating swithed on (-ON) 

All devices marked in eLan as:
- **lights** are reported to HA as light (controllable)
- **heating** are reported as temperature sensors and on/off sensor
