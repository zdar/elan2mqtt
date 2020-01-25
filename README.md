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

# Hass.IO
Copy elan2mqtt directory into Hass addons directory 

# Standalone
Use python to run main.py (check command line arguments)

# Device not supported by autodiscovery
Elan2mqqt has only limited autodiscovery for Home Assistant. If the device is not discovred by Home Assistant it can still be used using manual definition of MQTT template sensor. 
Status messages are using topic /eLan/device_mac_address/status
Command messages are using topic /eLan/device_mac_address/command

# Getting support for autodiscovery of your device
To get you device supported please open Issue ticket in github.
In ticke you have to provide:
- device type (prodict name)
- device typy as selected in eLan (light, heating,...)
- device info message*
- device status message*
- example of device commands*
and when possible home assistant MQTT sensor definition

(*) these can be captured using google web browser. Open developer tools (F12), log in into elan, use your device. In network tab you will see messages passing between browser and elan. Attach those relevant to you device.
