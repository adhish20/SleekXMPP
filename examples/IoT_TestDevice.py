#!/usr/bin/env python

"""
    SleekXMPP: The Sleek XMPP Library
    Implementation of xeps for Internet of Things
    http://wiki.xmpp.org/web/Tech_pages/IoT_systems
    Copyright (C) 2013 Sustainable Innovation, Joachim.lindborg@sust.se
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""




import os
import sys
# This can be used when you are in a test environment and need to make paths right
sys.path=['/Users/jocke/Dropbox/06_dev/SleekXMPP']+sys.path

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

#from sleekxmpp.exceptions import IqError, IqTimeout

SECONDS_BETEEN_CALLS_TO_PROVIDER = 30 #We will wait seconds between each call to a provider for data 

class IoT_TestDevice(sleekxmpp.ClientXMPP):

    """
    A simple IoT device that can act as server or client
    """
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.register_plugin('xep_0030')
        self.register_plugin('xep_0323')
        self.register_plugin('xep_0325')

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("changed_status",self.manage_status)

        self.device=None
        self.releaseMe=False
        self.beServer=True
        self.clientJID=None
        self.received=set()

    def datacallback(self,from_jid,result,nodeId=None,timestamp=None,fields=None,error_msg=None):
        """
        This method will be called when you ask another IoT device for data with the xep_0323
        se script below for the registration of the callback
        fields example
        [{'typename': 'numeric', 'unit': 'C', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'temperature', 'value': '13.5'},
        {'typename': 'numeric', 'unit': 'mb', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'barometer', 'value': '1015.0'},
        {'typename': 'numeric', 'unit': '%', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'humidity', 'value': '78.0'}]
        """
        
        if error_msg:
            logging.error('we got problem when recieving data %s', error_msg)
            return
        
        if result=='accepted':
            logging.debug("we got accepted from %s",from_jid)            
        elif result=='fields':
            logging.info("we got fields from %s with node %s",from_jid,nodeId)
            for field in fields:
                logging.info("Field %s %s %s",field['name'],field['value'],field['unit'])
        elif result=='done':
            logging.debug("we got  done from %s",from_jid)
        

    def beClientOrServer(self,server=True,clientJID=None ):
        if server:
            self.beServer=True
            self.clientJID=None
        else:
            self.beServer=False
            self.clientJID=clientJID
            

    def testForRelease(self):
        # todo thread safe
        return self.releaseMe

    def doReleaseMe(self):
        # todo thread safe
        self.releaseMe=True
        
    def addDevice(self, device):
        self.device=device

    def printRoster(self):
        logging.debug('Roster for %s' % self.boundjid.bare)
        groups = self.client_roster.groups()
        for group in groups:
            logging.debug('\n%s' % group)
            logging.debug('-' * 72)
            for jid in groups[group]:
                sub = self.client_roster[jid]['subscription']
                name = self.client_roster[jid]['name']
                if self.client_roster[jid]['name']:
                    logging.debug(' %s (%s) [%s]' % (name, jid, sub))
                else:
                    logging.debug(' %s [%s]' % (jid, sub))
                    
                connections = self.client_roster.presence(jid)
                for res, pres in connections.items():
                    show = 'available'
                    if pres['show']:
                        show = pres['show']
                    logging.debug('   - %s (%s)' % (res, show))
                    if pres['status']:
                        logging.debug('       %s' % pres['status'])

    def manage_status(self, event):
        logging.debug("got a status update" + str(event.getFrom()))
        self.printRoster()
        
    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        # tell your preffered friend that you are alive 
        self.send_message(mto='jocke@jabber.sust.se', mbody=self.boundjid.bare +' is now online use xep_323 stanza to talk to me')

        if not(self.beServer):
            logging.info('We are a client start asking %s for values' % self.clientJID)
            self.schedule('end', SECONDS_BETEEN_CALLS_TO_PROVIDER, self.askClientForValue, repeat=True, kwargs={})

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            logging.info("got normal chat message" + str(msg))
            ip=urlopen('http://icanhazip.com').read()
            msg.reply("Hi I am " + self.boundjid.full + " and I am on IP " + ip).send()
        else:
            logging.debug("got unknown message type %s", str(msg['type']))

    def askClientForValue(self):
        #need to find the full jid to call for data
        connections=self.client_roster.presence(self.clientJID)
        for res, pres in connections.items():
            # ask every session on the jid for data
            session=self['xep_0323'].request_data(self.boundjid.full,self.clientJID+"/"+res,self.datacallback, flags={"momentary":"true"})

            
class TheDevice(Device):
    """
    This is the actual device object that you will use to get information from your real hardware
    You will be called in the refresh method when someone is requesting information from you
    """
    def __init__(self,nodeId):
        Device.__init__(self,nodeId)
        self.counter=0

    def refresh(self,fields):
        """
        the implementation of the refresh method
        """
        self._set_momentary_timestamp(self._get_timestamp())
        self.counter=self.counter+1
        self._add_field_momentary_data( "Temperature", self.counter)
        
if __name__ == '__main__':

    # Setup the command line arguments.
    #
    # This script can act both as
    #   "server" an IoT device that can provide sensorinformation
    #   python IoT_TestDevice.py -j "poviderOfDataDevicedJID@yourdomain.com" -p "password" -n "TestIoT" --debug
    #
    #   "client" an IoT device or other party that would like to get data from another device every
    #   python IoT_TestDevice.py -j "loginJID@yourdomain.com" -p "password" -c "clienttocallfordata@yourdomain.com" --debu
    
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

    if opts.nodeid:

        # xmpp['xep_0030'].add_feature(feature='urn:xmpp:sn',
        # node=opts.nodeid,
        # jid=xmpp.boundjid.full)

        myDevice = TheDevice(opts.nodeid);
        # myDevice._add_field(name="Relay", typename="numeric", unit="Bool");
        myDevice._add_field(name="Temperature", typename="numeric", unit="C");
        myDevice._set_momentary_timestamp(myDevice._get_timestamp())
        myDevice._add_field_momentary_data("Temperature", "23.4", flags={"automaticReadout": "true","momentary":"true"});
        
        xmpp['xep_0323'].register_node(nodeId=opts.nodeid, device=myDevice, commTimeout=10);
        xmpp.beClientOrServer(server=True)
        while not(xmpp.testForRelease()):
            xmpp.connect()
            xmpp.process(block=True)    
            logging.debug("lost connection")
            
    if opts.sensorjid:
        logging.debug("will try to call another device for data")
        xmpp.beClientOrServer(server=False,clientJID=opts.sensorjid)
        xmpp.connect()
        xmpp.process(block=True)
        logging.debug("ready ending")
        
    else:
       print "noopp didn't happen"

