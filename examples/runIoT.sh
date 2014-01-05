#!/bin/bash
# put this in rc.local 

cd /home/pi/SleekXMPP/examples
/usr/bin/logger "starting IoT device server"
/usr/bin/python IoT_GPIODevice.py -j "JID@yourdomain.com" -p "password" -n "TestIoT" --debug 2>&1 | /usr/bin/logger > /dev/null

