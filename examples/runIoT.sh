#!/bin/bash
# put this in rc.local 

cd /home/pi/SleekXMPP/examples
logger "starting IoT device server"
python IoT_GPIODevice.py -j "sust9@jabber.sust.se" -p "QlpWkosust" -n "TestIoT" --debug 2>&1 | logger > /dev/null