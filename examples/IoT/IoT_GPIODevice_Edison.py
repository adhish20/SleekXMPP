#!/usr/bin/env python

"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.

    This eables The GPIO on a raspberry to be used as XMPP sensors
    the example is done with http://wiki.sweetpeas.se/index.php?title=Rpi_labbkitt 

    Must be run with root privileges to be able access GPIO

"""

import os
import sys

# This can be used when you are in a test environment and need to make paths right
sys.path=[os.path.join(os.path.dirname(__file__), '../..')]+sys.path

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
    

from sleekxmpp.plugins.xep_0323.device import Device as SensorDevice
from sleekxmpp.plugins.xep_0325.device import Device as ControlDevice

# import the Edison GPIO library
import mraa

#setup local led onboard
LED = mraa.Gpio(13)
LED.dir(mraa.DIR_OUT)

RELAY = mraa.Gpio(8)                                            
RELAY.dir(mraa.DIR_OUT)

PIR = mraa.Gpio(8)                                            
RELAY.dir(mraa.DIR_IN)

class IoT_TestDevice(sleekxmpp.ClientXMPP):

    """
    A simple IoT device that can act as server or client
    """
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("setReq", self.message)
        self.device=None
        self.releaseMe=False
        self.beServer=True
        self.clientJID=None



    def addDevice(self, device):
        self.device=device
        
    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        # tell your prefered friend that you are alive 
        self.send_message(mto='jabberjocke@jabber.se', mbody=self.boundjid.bare +' is now online use xep_323 stanza to talk to me')

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            # we are in a chat with a friend create an easy dialog
            logging.debug("got normal chat message" + str(msg))
            the_msg=msg['body'].lower().strip()
            if the_msg.startswith('hi'):
                ip=urlopen('http://icanhazip.com').read()
                msg.reply("Hi I am " + self.boundjid.full + " and I am on IP " + ip).send()
                
            elif the_msg.startswith('?'):
                logging.info('got a question ' + str(msg))
                self.device.refresh([])
                reply="My current values:\n"
                for key in self.device.momentary_data.keys():
                    reply+="%s=%s\n"%(key,str(self.device.momentary_data[key]['value']))
                msg.reply(reply).send()
                          
            elif the_msg.startswith('toggle') or the_msg.startswith('t'):
                logging.info('got a toggle ' + str(msg))
                if self.device.getrelay():
                    self.device.setrelay(False)
                else:
                    self.device.setrelay(True)
                    
            elif the_msg.find('=')>0:
                logging.debug('got a control chat message' + str(msg))
                (variable,value)=the_msg.split('=')
                logging.info('setting %s to %s' % (variable,value))
                self.device._set_field_value(variable,value)
            else:
                pass
        else:
            logging.debug("got unknown message type %s", str(msg['type']))

class TheDevice(SensorDevice,ControlDevice):
    """
    This is the actual device object that you will use to get information from your real hardware
    You will be called in the refresh method when someone is requesting information from you
    """

    def __init__(self,nodeId):
        SensorDevice.__init__(self,nodeId)
        ControlDevice.__init__(self,nodeId)

    def getrelay(self):
        return LED.read()
    
    def setrelay(self,state):
        if state:
            LED.write(1)
        else:
            LED.write(0)

    def getpir(self):
        return RELAY.read()

    def refresh(self,fields):
        """
        the implementation of the refresh method
        """
        self._set_momentary_timestamp(self._get_timestamp())
        if self.getpir():
            self._add_field_momentary_data("pir", 'true')
        else:
            self._add_field_momentary_data("pir", 'false')

        if self.getrelay():
            self._add_field_momentary_data("relay", 'true')
        else:
            self._add_field_momentary_data("relay", 'false')

    def _set_field_value(self, name,value):
        """ overrides the set field value from device to act on my local values
        """
        if name=="relay":
            if value=='true' or value=='1' or value==1 or value==True:
                self.setrelay(True)
            else:
                self.setrelay(False)
        elif name=="toggle":
            if self.getrelay():
                self.setrelay(False)
            else:
                self.setrelay(True)
        
if __name__ == '__main__':

    # Setup the command line arguments.
    #
    #
    #   python IoT_GPIODevice.py -j "serverjid@yourdomain.com" -p "password" -n "TestIoT" --debug
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

    myDevice = TheDevice(opts.nodeid);

    xmpp['xep_0323'].register_node(nodeId=opts.nodeid, device=myDevice, commTimeout=10)
    xmpp['xep_0325'].register_node(nodeId=opts.nodeid, device=myDevice, commTimeout=10)

    myDevice._add_field(name="relay", typename="boolean", unit="Bool")
    myDevice._add_control_field(name="relay", typename="boolean",value="false");
    myDevice._add_control_field(name="toggle", typename="boolean",value="false");
    myDevice._add_field(name="pir", typename="boolean", unit="Bool");
    myDevice._set_momentary_timestamp("2013-03-07T16:24:30")
    myDevice._add_field_momentary_data("relay", "false", flags={"automaticReadout": "true"})
    myDevice._add_field_momentary_data("pir", "false", flags={"automaticReadout": "true"})
    xmpp.addDevice(myDevice)

    xmpp.connect()
    xmpp.process(block=True)    
    logging.debug("lost connection")


