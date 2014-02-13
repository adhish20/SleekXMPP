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



import logging
import unittest
import distutils.core
import datetime

from glob import glob
from os.path import splitext, basename, join as pjoin
from optparse import OptionParser
optp = OptionParser()

from urllib import urlopen

# This can be used when you are in a test environment and need to make paths right if sleek is installed just comment this
sys.path=[os.path.join(os.path.dirname(__file__), '../..')]+sys.path
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
    
class IoT_TestDevice(sleekxmpp.ClientXMPP):

    """
    A simple IoT device that can act as server or client both on xep 323 and 325
    """
    
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.register_plugin('xep_0030')
        self.register_plugin('xep_0323')

        self.add_event_handler("session_start", self.session_start)

        #Some local status variables to use
        #self.device=None
        #self.releaseMe=False
        #self.beServer=True
        #self.clientJID=None
        #self.controlJID=None
        #self.received=set()
        #self.controlField=None
        #self.controlValue=None
        #self.delayValue=None
        #self.toggle=0

    def datacallback(self,from_jid,result,nodeId=None,timestamp=None,fields=None,error_msg=None):
        """
        This method will be called when you ask another IoT device for data with the xep_0323
        fields example, the flags session can be many
        [{'typename': 'numeric', 'unit': 'C', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'temperature', 'value': '13.5'},
        {'typename': 'numeric', 'unit': 'mb', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'barometer', 'value': '1015.0'},
        {'typename': 'numeric', 'unit': '%', 'flags': {'momentary': 'true', 'automaticReadout': 'true'}, 'name': 'humidity', 'value': '78.0'}]
        """
        
        if error_msg:
            logging.error('we got problem when recieving data %s', error_msg)
            return
        
        if result=='accepted':
            logging.debug("we got accepted from %s data will come",from_jid)            
        elif result=='fields':
            logging.info("we got fields from %s on node %s",from_jid,nodeId)
            for field in fields:
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
            logging.debug("we got  done from %s ",from_jid)
            if not(opts.delayvalue):
                # we should not do it again quit
                self.disconnect(wait=False)  
        else:
            logging.warn("we got unknown from %s %s",from_jid,result)

    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        # tell your preffered friend that you are alive 
        self.send_message(mto='jocke@jabber.sust.se', mbody=self.boundjid.bare +' is now online')

        logging.info('We are a client start asking %s for values' % opts.getsensorjid)
        if opts.delayvalue:
            self.schedule('end', float(opts.delayvalue), self.askClientForValue, repeat=True, kwargs={})
        else:
            self.schedule('end', float(5), self.askClientForValue, repeat=True, kwargs={})

    def askClientForValue(self):
        #need to find the full jid for each resource to call for data
        connections=self.client_roster.presence(opts.getsensorjid)
        logging.debug('IoT will call for data to '+ str(connections)+ " " + str(connections.keys()))
        for res in connections.keys():
            # ask every session on the jid for data
            if opts.field and opts.nodeid:
                session=self['xep_0323'].request_data(self.boundjid.full,opts.getsensorjid+"/"+res,self.datacallback, nodeIds=[opts.nodeid], fields=[opts.field],flags={"momentary":"true"})
            elif opts.nodeid:
                session=self['xep_0323'].request_data(self.boundjid.full,opts.getsensorjid+"/"+res,self.datacallback, nodeIds=[opts.nodeid],flags={"momentary":"true"})
            elif opts.field:
                session=self['xep_0323'].request_data(self.boundjid.full,opts.getsensorjid+"/"+res,self.datacallback, fields=[opts.field],flags={"momentary":"true"})
            else:
                session=self['xep_0323'].request_data(self.boundjid.full,opts.getsensorjid+"/"+res,self.datacallback, flags={"momentary":"true"})

               
if __name__ == '__main__':

    # Setup the command line arguments.
    #
    # This script is used to make readouts with the use of the xep 323
    #  Do a full readout once
    #  python IoT_Xep323ClientRead.py  -j "loginJID@yourdomain.com" -p "password" -g "clienttocallfordata@yourdomain.com" --debug
    #  full readout every 30 sek the repeted delay can be used on all calls
    #  python IoT_Xep323ClientRead.py  -j "loginJID@yourdomain.com" -p "password" -g "clienttocallfordata@yourdomain.com" --delay 30 --debug
    #  Readout of  a specific node
    #  python IoT_Xep323ClientRead.py  -j "loginJID@yourdomain.com" -p "password" -g "clienttocallfordata@yourdomain.com" --nodeid Device01 --debug
    #  Readout of a specific field 
    #  python IoT_Xep323ClientRead.py  -j "loginJID@yourdomain.com" -p "password" -g "clienttocallfordata@yourdomain.com" --field Humidity --debug
    #  Readout of a specific node and field 
    #  python IoT_Xep323ClientRead.py  -j "loginJID@yourdomain.com" -p "password" -g "clienttocallfordata@yourdomain.com" --nodeid Device01 --field Humidity --debug


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

    # IoT 
    optp.add_option("-g", "--getsensorjid", dest="getsensorjid",
                    help="Device to call for data on", default=None)
    optp.add_option("--nodeid", dest="nodeid",
                    help="The node to call for data on", default=None)
    optp.add_option("--field", dest="field",
                    help="Field to read from", default=None)
    optp.add_option("--delay", dest="delayvalue",
                    help="secondsdelay between reads", default=None)
    
    opts, args = optp.parse_args()

     # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
        
    xmpp = IoT_TestDevice(opts.jid,opts.password)

    xmpp.connect()
    xmpp.process(block=True)
    logging.debug("finished ending")
