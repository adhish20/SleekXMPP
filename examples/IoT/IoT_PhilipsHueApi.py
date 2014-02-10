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
import socket

# This can be used when you are in a test environment and need to make paths right
sys.path=[os.path.join(os.path.dirname(__file__), '../..'),os.path.join(os.path.dirname(__file__), '../../../phue')]+sys.path

from phue import Bridge
class DummyBridge():
    def set_light(self,dummy1,dummy2):
        logging.debug('dummybridge')
    def set_group(self,dummy1,dummy2):
        logging.debug('dummybridge')
    def get_light(self,dummy):
        logging.debug('dummybridge')
    def get_light(self,dummy):
        logging.debug('dummybridge')
        return {u'name': u'Attic hall', u'swversion': u'66010820', u'pointsymbol': {u'1': u'0f0000ffff00003333000033330000ffffffffff', u'3': u'none', u'2': u'none', u'5': u'none', u'4': u'none', u'7': u'none', u'6': u'none', u'8': u'none'}, u'state': {u'on': True, u'hue': 25400, u'colormode': u'hs', u'effect': u'none', u'alert': u'select', u'xy': [0.41110000000000002, 0.51649999999999996], u'reachable': True, u'bri': 254, u'sat': 254, u'ct': 293}, u'type': u'Extended color light', u'modelid': u'LCT001'}
    def get_group(self,dummy):
        logging.debug('dummybridge')
        return {u'action': {u'on': True, u'hue': 3000, u'colormode': u'xy', u'effect': u'none', u'xy': [0.64380000000000004, 0.34499999999999997], u'bri': 64, u'sat': 254, u'ct': 500}, u'lights': [u'1', u'2', u'3', u'4'], u'name': u'Lightset 0'}
                      
class BridgeContainer():
    
    def __init__(self,transitiontime=50,individual=None,ip='192.168.2.38'):
        try:
            self.mybridge=None    
            self.mybridge=Bridge(ip)
            self.mybridge.connect()
            self.mybridge.get_api()
        except Exception as e:
            logging.warn('failed to connect to HUE server')
            self.mybridge=DummyBridge()          
        self.transitiontime = transitiontime
        self.individual = None
        if individual:
            self.individual=int(individual)
        self.toggle()
        
    def setTransitionTime(self,value):
        # this should be the transistion time in seconds
        self.transitiontime = int(10 * float(value))

    def sendAll(self, hue=None, bri=None, sat=None, effect=None):
        lamp = self.individual or 0
        options = { }
        if hue is not None: options['hue'] = hue
        if bri is not None: options['bri'] = bri
        if sat is not None: options['sat'] = sat
        if effect is not None: options['effect'] = effect
        if self.transitiontime >= 0:
            options['transitiontime'] = self.transitiontime
        if self.individual:
            self.mybridge.set_light(self.individual, options)
        else:
                self.mybridge.set_group(0, options)

    def setEffect(self, value):
        self.sendAll(effect=effect)

    def setHue(self, value):
        self.sendAll(hue=value)

    def setBri(self, value):
        self.sendAll(bri=value)

    def setSat(self, value):
        self.sendAll(sat=value)

    def toggle(self):
        if self.individual:
            if self.mybridge.get_light(self.individual)['state']['on']:
                self.mybridge.set_light(self.individual, {'on': False})
            else:
                self.mybridge.set_light(self.individual, {'on': True})
        else:
            if self.mybridge.get_group(0)['action']['on']:
                self.mybridge.set_group(0, {'on': False})
            else:
                self.mybridge.set_group(0, {'on': True})

    def alert(self):
        if self.individual:
            self.mybridge.set_light(self.individual, {'alert':'select'})    
        else:
            self.mybridge.set_group(0, {'alert':'select'})    

bridge=None


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

#from sleekxmpp.exceptions import IqError, IqTimeout



class IoT_TestDevice(sleekxmpp.ClientXMPP):

    """
    A simple IoT device that can act as server or client both on xep 323 and 325
    """
    
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.register_plugin('xep_0030')
        self.register_plugin('xep_0323')
        self.register_plugin('xep_0325')
        self.register_plugin('xep_0199') # XMPP ping

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("changed_status",self.manage_status)

        #Some local status variables to use
        self.device=None
        self.releaseMe=False
        self.beServer=True
        self.clientJID=None
        self.controlJID=None
        self.received=set()
        self.controlField=None
        self.controlValue=None
        self.delayValue=None
        self.toggle=0

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
                if field.has_key('unit'):
                    logging.info("Field %s %s %s",field['name'],field['value'],field['unit'])
                else:
                    logging.info("Field %s %s",field['name'],field['value'])
        elif result=='done':
            logging.debug("we got  done from %s",from_jid)

    def controlcallback(self,from_jid,result,error_msg,nodeIds=None,fields=None):
        """
        Called as respons to a xep_0325 control message 
        """
        logging.info('Control callback from %s result %s error %s',from_jid,result,error_msg)

    def getformcallback(self,from_jid,result,error_msg):    
        """
        called as respons to a xep_0325 get Form iq message
        """
        logging.debug("IoT got a form "+str(result))
        
    def beClientOrServer(self,server=True,clientJID=None,controlJID=None,controlField=None,controlValue=None ):
        if server:
            self.beServer=True
            self.clientJID=None
        elif clientJID:
            self.beServer=False
            self.clientJID=clientJID            
        else:
            self.beServer=False
            self.controlJID=controlJID
            self.controlField=controlField
            self.controlValue=controlValue

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
        # self.send_message(mto='jocke@jabber.sust.se', mbody=self.boundjid.bare +' is now online use xep_323 stanza to talk to me')

        if not(self.beServer):
            if self.clientJID:
                logging.info('We are a client start asking %s for values' % self.clientJID)
                self.schedule('end', self.delayValue, self.askClientForValue, repeat=True, kwargs={})
            elif self.controlJID:
                logging.info('We are a control client set field %s to value %s on %s every %s',self.controlField,self.controlValue, self.controlJID, self.delayValue)
                self.schedule('end', self.delayValue, self.sendControlMessage, repeat=True, kwargs={})

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            if msg['body'].startswith('hi'):
                logging.info("got normal chat message" + str(msg))
                internetip=urlopen('http://icanhazip.com').read()
                localip=socket.gethostbyname(socket.gethostname())
                msg.reply("I am " + self.boundjid.full + " and I am on localIP " +localip +" and on internet " + internetip).send()
            elif msg['body'].startswith('A'):
                bridge.alert()
            elif msg['body'].startswith('?'):
                logging.debug('got a question ' + str(msg))
                self.device.refresh([])
                logging.debug('momentary values' + str(self.device.momentary_data))
                msg.reply(str(self.device.momentary_data)).send()
            elif msg['body'].startswith('T'):
                logging.debug('got a toggle ' + str(msg))
                bridge.toggle()
            elif msg['body'].find('=')>0:
                logging.debug('got a control' + str(msg))
                options = {}
                for option in msg['body'].split():
                    (name, value) = option.split('=')
                    logging.debug('setting %s to %s' % (name, value, ))
                    if name=="hue":
                        options['hue'] = int(value)
                    elif name=="bri":
                        options['bri'] = int(value)
                    elif name=="sat":
                        options['sat'] = int(value)
                    elif name=="time":
                        bridge.setTransitionTime(float(value))
                    elif name=="effect":
                        options['effect'] = value
                    elif name=="on":
                        bridge.toggle()
                if len(options) > 0:
                    bridge.sendAll(**options)
            else:
                logging.debug('message dropped ' +  msg['body'])
        else:
            logging.debug("got unknown message type %s", str(msg['type']))

    def askClientForValue(self):
        #need to find the full jid to call for data
        connections=self.client_roster.presence(self.clientJID)
        logging.debug('IoT will call for data to '+ str(connections))
        for res, pres in connections.items():
            # ask every session on the jid for data
            if self.controlField:
                session=self['xep_0323'].request_data(self.boundjid.full,self.clientJID+"/"+res,self.datacallback, fields=[self.controlField],flags={"momentary":"true"})
            else:
                session=self['xep_0323'].request_data(self.boundjid.full,self.clientJID+"/"+res,self.datacallback, flags={"momentary":"true"})

    def sendControlMessage(self):
        #need to find the full jid to call for data
        connections=self.client_roster.presence(self.controlJID)
        for res, pres in connections.items():
            # ask every session on the jid for data
            # session=self['xep_0325'].get_form(self.boundjid.full,self.controlJID+"/"+res,self.getformcallback)

            if not self.controlField:
                #no fields provided default to toggle a relay:
                if self.toggle:
                    self.toggle=0
                    logging.info('IoT will send relay true to '+ str(connections))
                    #session=self['xep_0325'].set_request(self.boundjid.full,self.controlJID+"/"+res,self.controlcallback,[("relay","boolean","1")])
                    session=self['xep_0325'].set_request(self.boundjid.full,self.controlJID+"/"+res,self.controlcallback,[("relay","boolean","true")])
                    #session=self['xep_0325'].set_command(self.boundjid.full,self.controlJID+"/"+res,[("relay","boolean","true")])
                else:
                    self.toggle=1
                    logging.info('IoT will send relay false to '+ str(connections))
                    #session=self['xep_0325'].set_request(self.boundjid.full,self.controlJID+"/"+res,self.controlcallback,[("relay","boolean","0")])
                    session=self['xep_0325'].set_request(self.boundjid.full,self.controlJID+"/"+res,self.controlcallback,[("relay","boolean","false")])
                    #session=self['xep_0325'].set_command(self.boundjid.full,self.controlJID+"/"+res,[("relay","boolean","false")])
            else:
                logging.info('IoT will set %s to %s on to %s'%(self.controlField,self.controlValue,str(connections)))
                session=self['xep_0325'].set_request(self.boundjid.full,self.controlJID+"/"+res,self.controlcallback,[(self.controlField,"boolean",self.controlValue)])
            
class TheDevice(SensorDevice,ControlDevice):
    """
    Xep 323 SensorDevice
    This is the actual device object that you will use to get information from your real hardware
    You will be called in the refresh method when someone is requesting information from you

    xep 325 ControlDevice
    This 
    """
    def __init__(self,nodeId):
        SensorDevice.__init__(self,nodeId)
        ControlDevice.__init__(self,nodeId)
        self.counter=0
        self.relay=0


    def refresh(self,fields):
        """
        the implementation of the refresh method
        """
        self._set_momentary_timestamp(self._get_timestamp())
        self.counter=self.counter+1
        self._add_field_momentary_data("Counter", self.counter)
        self._add_field_momentary_data("Relay", self.relay)

    def _set_field_value(self, name,value):
        """ overrides the set field value from device to act on my local values                                            
        """
        
        if name=="hue":
            bridge.setHue(int(value))
        elif name=="bri":
            bridge.setBri(int(value))
        elif name=="sat":
            bridge.setSat(int(value))
        elif name=="toggle":
            bridge.toggle()
        elif name=="on":
            bridge.setOn(int(value))

        
if __name__ == '__main__':

    # Setup the command line arguments.
    #
    # This script is an evolution from the IoT_TestDevice to integrate the web API from Philips HUE
    # Start this script in several instanses to control different lamps or the whole group
    # 
    #   Start with control of lamp 2
    #   python IoT_PhilipsHueApi.py -j "onelampJID@yourdomain.com" -p "password" -n "Lamp1" --individual 2 --bridgeip "192.168.2.22" --debug
    #
    #   starting without individual creates control of group 0
    #   python IoT_PhilipsHueApi.py -j "alllampsJID@yourdomain.com" -p "password" -n "LampGroup0" --bridgeip "192.168.2.22" --debug
    #
    #   TODO: clean up inheritage from IoT_TestDevice
    
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
    optp.add_option("-n", "--nodeid", dest="nodeid",
                    help="Server (Provider) I am a device that can be called for data or send control to", default=None)
    optp.add_option("-g", "--getsensorjid", dest="getsensorjid",
                    help="Device to call for data on", default=None)
    optp.add_option("-c", "--controljid", dest="controljid",
                    help="Device to call for data on", default=None)
    optp.add_option("--field", dest="controlfield",
                    help="Field to act upon", default=None)
    optp.add_option("--value", dest="controlvalue",
                    help="control value", default=None)
    optp.add_option("--delay", dest="delayvalue",
                    help="secondsdelay between reads or controls", default=30)
    optp.add_option("--individual", dest="individual",
                    help="setting the control to an individual", default=None)
    optp.add_option("--bridgeip", dest="bridgeip",
                    help="This is where the bridge is", default='192.168.1.42')
    
    opts, args = optp.parse_args()

     # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")

    logging.debug("setting an individual " + str(opts.individual))
    bridge=BridgeContainer(individual=opts.individual,ip=opts.bridgeip)
        
    xmpp = IoT_TestDevice(opts.jid,opts.password)
    xmpp.delayValue=int(opts.delayvalue)
    logging.debug("DELAY " + str(int(opts.delayvalue)) + "  " + str(xmpp.delayValue))
    
    if opts.nodeid:
        # prepare the IoT_TestDevice to be a provider of data and be able to recieve control commands
        # xmpp['xep_0030'].add_feature(feature='urn:xmpp:sn',
        # node=opts.nodeid,
        # jid=xmpp.boundjid.full)
        
        # Instansiate the device object
        myDevice = TheDevice(opts.nodeid);
        myDevice._add_field(name="Relay", typename="numeric", unit="Bool");
        myDevice._add_control_field(name="transitiontime", typename="long", value=50);
        myDevice._add_control_field(name="hue", typename="long", value=1);
        myDevice._add_control_field(name="on", typename="boolean", value=1);
        myDevice._add_control_field(name="toggle", typename="boolean", value=1);
        myDevice._add_control_field(name="bri", typename="long", value=1);
        myDevice._add_control_field(name="sat", typename="long", value=1);
        myDevice._add_field(name="Counter", typename="long", unit="Count");
        myDevice._set_momentary_timestamp(myDevice._get_timestamp())
        myDevice._add_field_momentary_data("hue", "0", flags={"automaticReadout": "true","momentary":"true"});
        myDevice._add_field_momentary_data("on", "0", flags={"automaticReadout": "true","momentary":"true"});
        
        xmpp['xep_0323'].register_node(nodeId=opts.nodeid, device=myDevice, commTimeout=10);
        xmpp['xep_0325'].register_node(nodeId=opts.nodeid, device=myDevice, commTimeout=10);

        xmpp.beClientOrServer(server=True)
        xmpp.connect()
        xmpp.process(block=True)    
        logging.debug("lost connection")
            
    elif opts.getsensorjid:
        logging.debug("will try to call another device for data")
        xmpp.beClientOrServer(server=False,clientJID=opts.getsensorjid)
        xmpp.connect()
        xmpp.process(block=True)
        logging.debug("ready ending")

    elif opts.controljid:
        logging.debug("will try to send control message to another device")
        xmpp.beClientOrServer(server=False,controlJID=opts.controljid,controlField=opts.controlfield,controlValue=opts.controlvalue)
        xmpp.connect()
        xmpp.process(block=True)
        logging.debug("ready ending")
    else:
       print "noopp didn't happen"