#!/usr/bin/env python

"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.

    This creates an example of accessing a Kamstrup heat energy metere

    depends on the pyserial for serial support

"""

import os
import sys
# This can be used when you are in a test environment and need to make paths right
sys.path=['/home/pi/SleekXMPP']+sys.path
sys.path=['/home/pi/PyKamstrup']+sys.path

import serial
import kamstrup

import logging
import unittest
import distutils.core
import datetime

from glob import glob
from os.path import splitext, basename, join as pjoin
from optparse import OptionParser
from urllib import urlopen

import sleekxmpp
# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input
    
from sleekxmpp.plugins.xep_0323.device import Device
import RPi.GPIO as GPIO

class IoT_TestDevice(sleekxmpp.ClientXMPP):

    """
    A simple IoT device that can act as server or client
    """
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.device=None
        self.releaseMe=False
        self.beServer=True
        self.clientJID=None



    def addDevice(self, device):
        self.device=device
        
    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        # tell your preffered friend that you are alive 
        self.send_message(mto='jocke@jabber.sust.se', mbody=self.boundjid.bare +' is now online use xep_323 stanza to talk to me')

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            logging.debug("got normal chat message" + str(msg))
            if msg['body'].startswith('hi'):
                ip=urlopen('http://icanhazip.com').read()
                msg.reply("Hi I am " + self.boundjid.full + " and I am on IP " + ip).send()
            elif msg['body'].startswith('?'):
                logging.debug('got a question ' + str(msg))
                self.device.refresh([])
                logging.debug('momentary values' + str(self.device.momentary_data))
                msg.reply(str(self.device.momentary_data)).send()
            elif msg['body'].startswith('T'):
                logging.debug('got a toggle ' + str(msg))
                if self.device.getrelay():
                    self.device.setrelay(False)
                else:
                    self.device.setrelay(True)
            elif msg['body'].find('=')>0:
                logging.debug('got a control' + str(msg))
                (variable,value)=msg['body'].split('=')
                logging.debug('setting %s to %s' % (variable,value))
                
            else:
                pass
        else:
            logging.debug("got unknown message type %s", str(msg['type']))

class TheDevice(Device):
    """
    This is the actual device object that you will use to get information from your real hardware
    You will be called in the refresh method when someone is requesting information from you
    """

    def __init__(self,nodeId, serialport):
        Device.__init__(self,nodeId)
        self.meter=kamstrup.kamstrup(serial_port=serialport)
        self.meter_reg = kamstrup.kamstrup_multical402_var
        self.meter.setBaudrate(self.meter_reg[0]['baudrate'])
        self.firstread=True
            
    def refresh(self,fields):
        """
        the implementation of the refresh method
        """
        # for i in range (1,0x100):
        self._set_momentary_timestamp(self._get_timestamp())


        for i in self.meter_reg[1]:
            x,y =self.meter.readvar(i)
            if self.firstread:
                self._add_field(name=self.meter_reg[1][i], typename="numeric", unit=str(y));
            self._add_field_momentary_data(self.meter_reg[1][i], str(x)) 

        #    logging.debug("%-25s %s %s" , self.meter_reg[1][i], x, y)
        

        #self._add_field_momentary_data("pir", self.getpir()) 
        #self._add_field_momentary_data("relay", self.getrelay()) 

        
if __name__ == '__main__':

    # Setup the command line arguments.
    #
    #
    #   python IoT_KamstrupDevice.py -j "serverjid@yourdomain.com" -p "password" -n "TestIoT" --debug
    #
    
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)
    optp.add_option('-t', '--pingto', help='set jid to ping',
                    action='store', type='string', dest='pingjid',
                    default=None)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    # IoT test
    optp.add_option("-c", "--sensorjid", dest="sensorjid",
                    help="Another device to call for data on", default=None)
    optp.add_option("-n", "--nodeid", dest="nodeid",
                    help="I am a device get ready to be called", default=None)
    optp.add_option("-s", "--serial", dest="serialport",
                    help="The serialport we need", default="/dev/ttyUSB0")
    
    opts, args = optp.parse_args()

     # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
        

    xmpp = IoT_TestDevice(opts.jid,opts.password)
    xmpp.register_plugin('xep_0030')
    xmpp.register_plugin('xep_0323')
    xmpp.register_plugin('xep_0325')

    myDevice = TheDevice(opts.nodeid, opts.serialport);

    xmpp.addDevice(myDevice)

    xmpp['xep_0323'].register_node(nodeId=opts.nodeid, device=myDevice, commTimeout=10);
    
    xmpp.connect()
    xmpp.process(block=True)    
    logging.debug("lost connection")


