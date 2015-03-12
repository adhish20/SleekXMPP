#!/bin/bash
# put this in rc.local 

/usr/bin/logger "starting IoT device server"
cd /home/pi/SleekXMPP/examples/IoT
/usr/bin/logger "starting IoT device server"
/usr/bin/python IoT_PhilipsHueApi.py -j john@ik.nu -p awesomehat -n 'John'  --individual 1 2>&1 | /usr/bin/logger > /dev/null &
/usr/bin/python IoT_PhilipsHueApi.py -j paul@ik.nu -p awesomehat -n 'Paul'  --individual 2 2>&1 | /usr/bin/logger > /dev/null &
/usr/bin/python IoT_PhilipsHueApi.py -j ringo@ik.nu -p awesomehat -n 'Ringo'  --individual 3 2>&1 | /usr/bin/logger > /dev/null &
/usr/bin/python IoT_PhilipsHueApi.py -j george@ik.nu -p awesomehat -n 'George'  --individual 4 2>&1 | /usr/bin/logger > /dev/null &
/usr/bin/python IoT_PhilipsHueApi.py -j beatles@ik.nu -p awesomehat -n 'Beatles'  2>&1 | /usr/bin/logger > /dev/null &
#/usr/bin/python IoT_GPIODevice.py -j "JID@yourdomain.com" -p "password" -n "TestIoT" --debug 2>&1 | /usr/bin/logger > /dev/null

