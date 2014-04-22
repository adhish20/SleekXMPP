#!/usr/bin/env python
#
# Author: Jonas Jonsson <jonas@websystem.se>

import serial
import time

class icp(object):

    def __init__(self, port, address, speed=9600):
        self.s = serial.Serial(port, speed, timeout=1)
        self.address = address

        self.debug = False

    def csum(self, buf):
        """Calculate the checksum for buf and return it as a hexadecimal
        string"""
        s = 0
        for i in buf:
            s += ord(i)
        return "%02x" % (s & 0xff)

    def send(self, leading, command):
        buf = "%s%02x%s" % (leading, self.address, command)
        if self.debug:
            print("> " + buf + "\r")
        self.s.write(buf + "\r")

    def read_response(self):
        """Read data until 0x0d is received or a timeout"""
        buf = self.s.read(1)
        while ord(buf[-1]) != 0x0d:
            buf += self.s.read(1)

        if self.debug:
            print("< %s" % buf)

        return buf

    def read_module_name(self):
        self.send("$", "M")
        resp = self.read_response()

        if resp[0] != '!':
            print "Failed to read module name"
            return None

        return resp[3:-1]

    def read_firmware_version(self):
        self.send("$", "F")
        resp = self.read_response()

        if resp[0] != '!':
            print("Failed to read firmware version")
            return None

        return resp[3:-1]

    def set_digital_output(self, ios, value):
        if ios <= 4:
            self.send("@", "%01X" % value)
        elif ios <= 8:
            self.send("@", "%02X" % value)
        elif ios <= 16:
            self.send("@", "%04X" % value)
        resp = self.read_response()

        if resp[0] != '>':
            print("Failed to set digital output")

        return resp[0] == '>'
    def read_digital_io_status(self):
        self.send("$", "6")
        resp = self.read_response()

        if resp[0] != '!':
            print("Failed to read digital I/O status")
            return None

        return int(resp[3:-3], 16)

    def read_all_analog(self):
        self.send("#", "")
        resp = self.read_response()

        if resp[0] != '>':
            print("Failed to read all analog ")
            return None

        # FIXME
        return True

    def read_single_analog(self, index):
        self.send("#", "%X" % index)
        resp = self.read_response()

        if resp[0] != '>':
            print("Failed to read single analog ")
            return None

        return float(resp[1:-1])

    def read_module_configuration(self):
        self.send("$", "2")
        resp = self.read_response()

        if resp[0] != '!':
            print("Failed to read module configuration")
            return None

        return resp[3:-1]

    def close(self):
        self.s.close()


def read_all():
    for i in (2, 3, 4, 5):
        d = icp("/dev/ttyUSB0", i, 9600)
        print("Module name 0x%02x: %s" % (i, d.read_module_name()))
        print("Firmware version 0x%02x: %s" % (i, d.read_firmware_version()))
        d.close()

def monitor_input_7044d():
    d = icp("/dev/ttyUSB0", 4, 9600)
    print("Module name 0x%02x: %s" % (4, d.read_module_name()))
    print("Firmware version 0x%02x: %s" % (4, d.read_firmware_version()))

    v_old = None
    print("Monitor Digital Input")
    while True:
        v = d.read_digital_io_status() & 0x000f
        if v != v_old:
            v_old = v
            print("Digital I/O status: %s" % bin(v))
        time.sleep(0.1)

    d.close()

def monitor_temperature_7033():
    d = icp("/dev/ttyUSB0", 3, 9600)
    print("Module name 0x%02x: %s" % (3, d.read_module_name()))
    print("Firmware version 0x%02x: %s" % (3, d.read_firmware_version()))

    v_old0 = None
    v_old1 = None
    while True:
        v0 = d.read_single_analog(0)
        v1 = d.read_single_analog(1)
        if v0 != v_old0 or v1 != v_old1:
            v_old0 = v0
            v_old1 = v1
            print(u"%.2f \u2103\t\t%.2f \u2103" % (v0, v1))
        time.sleep(0.1)

if __name__ == "__main__":
    #read_all()
    #monitor_input_7044d()
    monitor_temperature_7033()
