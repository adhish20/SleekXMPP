import os
import sys
import socket

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

from IoT_Logger import Logger as Logger

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
        self.logger=Logger()
        self.releaseMe=False
        self.beServer=True
        self.clientJID=None
        self.controlJID=None
        self.received=set()
        self.controlField=None
        self.controlValue=None
        self.controlType=None
        self.delayValue=None
        self.toggle=0

    def datacallback(self,from_jid,result,nodeId=None,timestamp=None,fields=None,error_msg=None):
        """
        This method will be called when you ask another IoT device for data with the xep_0323
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
            logging.info("we got fields from %s on node %s",from_jid,nodeId)
            for field in fields:
                # Storing in Log
                self.logger.LocalStore(from_jid, timestamp, nodeId, field['typename'], field['name'], field['value'], field['unit'])
                info="(%s %s %s) " % (nodeId,field['name'],field['value'])
                if field.has_key('unit'):
                    info+="%s " % field['unit']
                if field.has_key('flags'):
                    info+="["
                    for flag in field['flags'].keys():
                        info+=flag + ","
                    info+="]"
                logging.info(info)
        elif result=='done':
            logging.debug("we got  done from %s",from_jid)
        
    def beClientOrServer(self, clientJID=None):
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
            if self.clientJID:
                logging.info('We are a client start asking %s for values' % self.clientJID)
                self.schedule('end', self.delayValue, self.askClientForValue, repeat=True, kwargs={})

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            if msg['body'].startswith('hi'):
                logging.info("got normal chat message" + str(msg))
                internetip=urlopen('http://icanhazip.com').read()
                localip=socket.gethostbyname(socket.gethostname())
                msg.reply("I am " + self.boundjid.full + " and I am on localIP " +localip +" and on internet " + internetip).send()
            elif msg['body'].startswith('?'):
                logging.debug('got a question ' + str(msg))
                self.device.refresh([])
                logging.debug('momentary values' + str(self.device.momentary_data))
                msg.reply(str(self.device.momentary_data)).send()
            elif msg['body'].startswith('T'):
                logging.debug('got a toggle ' + str(msg))
                if self.device.relay:
                    self.device.relay=False
                else:
                    self.device.srelay=True
            elif msg['body'].find('=')>0:
                logging.debug('got a control' + str(msg))
                (variable,value)=msg['body'].split('=')
                logging.debug('setting %s to %s' % (variable,value))
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
            if res!=self.boundjid.resource:
                #ignoring myself
                if self.controlField:
                    session=self['xep_0323'].request_data(self.boundjid.full,self.clientJID+"/"+res,self.datacallback, fields=[self.controlField],flags={"momentary":"true"})
                else:
                    session=self['xep_0323'].request_data(self.boundjid.full,self.clientJID+"/"+res,self.datacallback, flags={"momentary":"true"})
            
class TheDevice(SensorDevice):
    """
    Xep 323 SensorDevice
    This is the actual device object that you will use to get information from your real hardware
    You will be called in the refresh method when someone is requesting information from you
    """
    def __init__(self,nodeId):
        SensorDevice.__init__(self,nodeId)

    def get_history(self, session, fields, from_flag, to_flag, callback):

        field = fields[0]
        timestamp, node, typename, name, value, unit = self.logger.LocalRetrieve(opts.jid, field, from_flag, to_flag)
        ts_block = {}
        field_block = {"name": name[i], 
                        "type": typename[i], 
                        "unit": unit[i],
                        "value": value[i], 
                        "flags": {'historical': 'true', 'automaticReadout': 'true'}}
        ts_block["timestamp"] = timestamp[i]
        ts_block["fields"] = field_block

        callback(session, result="fields", nodeId=self.nodeId, timestamp_block=ts_block);
        return
        
if __name__ == '__main__':
    """
    To Run :
    python IoT_HistoryLogger.py -j device1@xmpp.xmpp-iot.org -p d3vic31 --phost proxy.iiit.ac.in --pport 8080 --delay 10 --debug
    """

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


    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("--phost", dest="proxy_host",
                    help="Proxy hostname", default = None)
    optp.add_option("--pport", dest="proxy_port",
                    help="Proxy port", default = None)
    optp.add_option("--puser", dest="proxy_user",
                    help="Proxy username", default = None)
    optp.add_option("--ppass", dest="proxy_pass",
                    help="Proxy password", default = None)

    optp.add_option("--delay", dest="delayvalue",
                    help="secondsdelay between reads or controls", default=30)
    
    opts, args = optp.parse_args()

     # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = raw_input("Password: ")
        
    xmpp = IoT_TestDevice(opts.jid,opts.password)
    xmpp.delayValue=int(opts.delayvalue)
    logging.debug("DELAY " + str(int(opts.delayvalue)) + "  " + str(xmpp.delayValue))
    
    if opts.proxy_host:
        xmpp.use_proxy = True
        xmpp.proxy_config = {
            'host' : opts.proxy_host,
            'port' : int(opts.proxy_port),
            'username' : opts.proxy_user,
            'password' : opts.proxy_pass}
    
    logging.debug("will try to call another device for data")
    myDevice = TheDevice("history");
    xmpp.device=myDevice
    xmpp['xep_0323'].register_node(nodeId="history", device=myDevice, commTimeout=10);
    xmpp.beClientOrServer(clientJID=opts.jid)
    xmpp.connect()
    xmpp.process(block=True)
    logging.debug("ready ending")
