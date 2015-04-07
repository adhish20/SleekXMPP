#!/usr/bin/env python

"""
    Implementation of GUI for  IoT_TestDevice
    Copyright (C) 2015, Adhish Singla
    This file is part of SleekXMPP.

    All rights reserved.
"""

import sys

from PyQt4 import QtGui

from IoT_TestDevice import *

class Profile(QtGui.QWidget):

    def __init__(self):
        super(Profile, self).__init__()
        self.tab = QtGui.QTabWidget()
        self.login = QtGui.QWidget()
        self.option = QtGui.QWidget()
        self.proxy = QtGui.QWidget()
        self.add = QtGui.QWidget()
        self.xmpp = None
        self.running = 0
        self.initUI()

    def initUI(self):
        """ Main UI """
        # Tabs
        self.tab.addTab(self.login, "Login")
        self.tab.addTab(self.option, "Options")
        self.tab.addTab(self.proxy, "Proxy")
        self.tab.addTab(self.add, "Add New")

        # Login Tab
        # Login Labels
        self.login.username = QtGui.QLabel(self.login)
        self.login.username.setText('Username')

        self.login.password = QtGui.QLabel(self.login)
        self.login.password.setText('Password')

        # Login Variables
        self.login.Username = QtGui.QLineEdit(self.login)

        self.login.Password = QtGui.QLineEdit(self.login)
        self.login.Password.setEchoMode(QtGui.QLineEdit.Password)

        # Login Grid
        self.login.grid = QtGui.QGridLayout()
        self.login.grid.setSpacing(10)

        self.login.grid.addWidget(self.login.username,1,0)
        self.login.grid.addWidget(self.login.password,2,0)
        self.login.grid.addWidget(self.login.Username,1,1)
        self.login.grid.addWidget(self.login.Password,2,1)

        self.login.setLayout(self.login.grid)

        # Option Tab
        # Option Labels
        self.option.nodeId = QtGui.QLabel(self.option)
        self.option.nodeId.setText('Node ID')
        
        self.option.sensorId = QtGui.QLabel(self.option)
        self.option.sensorId.setText('Sensor ID')

        self.option.controlId = QtGui.QLabel(self.option)
        self.option.controlId.setText('Control ID')

        self.option.controlField = QtGui.QLabel(self.option)
        self.option.controlField.setText('Control Field')

        self.option.controlValue = QtGui.QLabel(self.option)
        self.option.controlValue.setText('Control Value')
    
        self.option.delayValue = QtGui.QLabel(self.option)
        self.option.delayValue.setText('Delay Value')

        # Option Variables
        self.option.NodeId = QtGui.QLineEdit(self.option)
        self.option.SensorId = QtGui.QLineEdit(self.option)
        self.option.ControlId = QtGui.QLineEdit(self.option)
        self.option.ControlField = QtGui.QLineEdit(self.option)
        self.option.ControlValue = QtGui.QLineEdit(self.option)
        self.option.DelayValue = QtGui.QLineEdit(self.option)

        # Option Grid
        self.option.grid = QtGui.QGridLayout()
        self.option.grid.setSpacing(10)

        self.option.grid.addWidget(self.option.nodeId,1,0)
        self.option.grid.addWidget(self.option.sensorId,2,0)
        self.option.grid.addWidget(self.option.controlId,3,0)
        self.option.grid.addWidget(self.option.controlField,4,0)
        self.option.grid.addWidget(self.option.controlValue,5,0)
        self.option.grid.addWidget(self.option.delayValue,6,0)
        self.option.grid.addWidget(self.option.NodeId,1,1)
        self.option.grid.addWidget(self.option.SensorId,2,1)
        self.option.grid.addWidget(self.option.ControlId,3,1)
        self.option.grid.addWidget(self.option.ControlField,4,1)
        self.option.grid.addWidget(self.option.ControlValue,5,1)
        self.option.grid.addWidget(self.option.DelayValue,6,1)

        self.option.setLayout(self.option.grid)

        # Proxy Tab
        # Proxy Labels
        self.proxy.host = QtGui.QLabel(self.proxy)
        self.proxy.host.setText('Host Name')

        self.proxy.port = QtGui.QLabel(self.proxy)
        self.proxy.port.setText('Port')

        self.proxy.username = QtGui.QLabel(self.proxy)
        self.proxy.username.setText('Username')

        self.proxy.password = QtGui.QLabel(self.proxy)
        self.proxy.password.setText('Password')

        # Proxy Variables
        self.proxy.HostName = QtGui.QLineEdit(self.proxy)
        self.proxy.Port = QtGui.QLineEdit(self.proxy)
        self.proxy.Username = QtGui.QLineEdit(self.proxy)
        self.proxy.Password = QtGui.QLineEdit(self.proxy)
        self.proxy.Password.setEchoMode(QtGui.QLineEdit.Password)

        # Proxy Grid
        self.proxy.grid = QtGui.QGridLayout()
        self.proxy.grid.setSpacing(10)

        self.proxy.grid.addWidget(self.proxy.host,1,0)
        self.proxy.grid.addWidget(self.proxy.port,2,0)
        self.proxy.grid.addWidget(self.proxy.username,3,0)
        self.proxy.grid.addWidget(self.proxy.password,4,0)
        self.proxy.grid.addWidget(self.proxy.HostName,1,1)
        self.proxy.grid.addWidget(self.proxy.Port,2,1)
        self.proxy.grid.addWidget(self.proxy.Username,3,1)
        self.proxy.grid.addWidget(self.proxy.Password,4,1)

        self.proxy.setLayout(self.proxy.grid)

        # Add New Tab
        # Add New Labels
        self.add.jid = QtGui.QLabel(self.add)
        self.add.jid.setText('Friend\'s JID')

        self.add.name = QtGui.QLabel(self.add)
        self.add.name.setText('Friend\'s Name')

        self.add.group = QtGui.QLabel(self.add)
        self.add.group.setText('Group Name')

        self.add.subscription = QtGui.QLabel(self.add)
        self.add.subscription.setText('Subscription')

        # Add New Variables
        self.add.Jid = QtGui.QLineEdit(self.add)

        self.add.Name = QtGui.QLineEdit(self.add)

        self.add.Group = QtGui.QLineEdit(self.add)

        self.add.Subscription = QtGui.QLineEdit(self.add)

        #Add New Buttons
        self.add.Button = QtGui.QPushButton(self.add)
        self.add.Button.setText('Make Friend')
        self.add.Button.clicked.connect(self.makeFriend)

        # Add New Grid
        self.add.grid = QtGui.QGridLayout()
        self.add.grid.setSpacing(10)

        self.add.grid.addWidget(self.add.jid,1,0)
        self.add.grid.addWidget(self.add.name,2,0)
        self.add.grid.addWidget(self.add.group,3,0)
        self.add.grid.addWidget(self.add.subscription,4,0)
        self.add.grid.addWidget(self.add.Jid,1,1)
        self.add.grid.addWidget(self.add.Name,2,1)
        self.add.grid.addWidget(self.add.Group,3,1)
        self.add.grid.addWidget(self.add.Subscription,4,1)
        self.add.grid.addWidget(self.add.Button,5,1)

        self.add.setLayout(self.add.grid)

        # Buttons
        self.Login = QtGui.QPushButton(self)
        self.Login.setText('Login')
        self.Login.clicked.connect(self.Run)

        self.Relay = QtGui.QPushButton(self)
        self.Relay.setText('Relay')
        self.Relay.clicked.connect(self.RelayChange)

        # Horizontal Layouts
        self.hbox1 = QtGui.QHBoxLayout()
        self.hbox1.addWidget(self.Login)
        self.hbox1.addWidget(self.Relay)

        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.tab)

        # Vertical Layout
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.vbox.addLayout(self.hbox1)

        # Main Layout
        self.setLayout(self.vbox)

        self.setGeometry(300,280, 300, 250)
        self.setWindowTitle('Profile')
        self.show()

    def Run(self):
        if self.running == 0:
            self.running = 1
            # Setup logging.
            logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)-8s %(message)s')

            if str(self.login.Username.text()) == "":
                #opts.jid = raw_input("Username: ")
                return
            if str(self.login.Username.text()) == "":
                #opts.password = getpass.getpass("Password: ")
                return

            self.xmpp = IoT_TestDevice(str(self.login.Username.text()),str(self.login.Password.text()))


            """Auto Authorizing set to true for making new friends"""
            self.xmpp.auto_authorize = True
            self.xmpp.auto_subscribe = True

            if str(self.option.DelayValue.text()) == "":
                self.xmpp.delayValue = 30
                logging.debug("DELAY " + str(int(30)) + "  " + str(self.xmpp.delayValue))
            else:
                self.xmpp.delayValue=int(self.option.DelayValue.text())
                logging.debug("DELAY " + str(int(self.option.DelayValue.text())) + "  " + str(self.xmpp.delayValue))

            if str(self.proxy.HostName.text()) != "":
                self.xmpp.use_proxy = True

                if str(self.proxy.Username.text()) == "":
                    self.user = None
                else:
                    self.user = str(self.proxy.Username.text())

                if str(self.proxy.Password.text()) == "":
                    self.password = None
                else:
                    self.password = str(self.proxy.Password.text())

                self.xmpp.proxy_config = {
                    'host' : str(self.proxy.HostName.text()),
                    'port' : int(self.proxy.Port.text()),
                    'username' : self.user,
                    'password' : self.password}

            if str(self.option.NodeId.text()) == "":
                self.NodeId = None
            else:
                self.NodeId = str(self.option.NodeId.text())

            if str(self.option.SensorId.text()) == "":
                self.SensorId = None
            else:
                self.SensorId = str(self.option.SensorId.text())

            if str(self.option.ControlId.text()) == "":
                self.ControlId = None
            else:
                self.ControlId = str(self.option.ControlId.text())

            if str(self.option.ControlField.text()) == "":
                self.ControlField = None
            else:
                self.ControlField = str(self.option.ControlField.text())

            if str(self.option.ControlValue.text()) == "":
                self.ControlValue = None
            else:
                self.ControlValue = str(self.option.ControlValue.text())

            if self.NodeId:
                # prepare the IoT_TestDevice to be a provider of data and be able to recieve control commands
                # self.xmpp['xep_0030'].add_feature(feature='urn:self.xmpp:sn',
                # node=opts.nodeid,
                # jid=self.xmpp.boundjid.full)

                # Instansiate the device object
                self.myDevice = TheDevice(self.NodeId);
                self.myDevice._add_field(name = "Relay", typename = "numeric", unit = "Bool");
                self.myDevice._add_control_field(name = "Relay", typename = "numeric", value = 1);
                self.myDevice._add_field(name = "Counter", typename = "numeric", unit = "Count");
                self.myDevice._set_momentary_timestamp(self.myDevice._get_timestamp())
                self.myDevice._add_field_momentary_data("Counter", "0", flags ={"automaticReadout": "true","momentary":"true"});
                self.myDevice._add_field_momentary_data("Relay", "0", flags ={"automaticReadout": "true","momentary":"true" , "writeable":"true"});

                self.xmpp['xep_0323'].register_node(nodeId = self.NodeId, device = self.myDevice, commTimeout = 10);
                self.xmpp['xep_0325'].register_node(nodeId = self.NodeId, device = self.myDevice, commTimeout = 10);
                self.xmpp.beClientOrServer(server = True)
                # while not(self.xmpp.testForRelease())
                self.xmpp.connect()
                self.xmpp.process(threaded = True)
                logging.debug("ready ending")

            elif self.SensorId:
                logging.debug("will try to call another device for data")
                self.xmpp.beClientOrServer(server = False,clientJID = self.SensorId)
                self.xmpp.connect()
                self.xmpp.process(threaded = True)
                logging.debug("ready ending")

            elif self.ControlId:
                logging.debug("will try to send control message to another device")
                self.xmpp.beClientOrServer(server = False,controlJID = self.ControlId,
                    controlField = self.ControlField,controlValue = self.ControlValue)
                self.xmpp.connect()
                self.xmpp.process(threaded = True)
                logging.debug("ready ending")

            else:
                print "noopp didn't happen"

    def RelayChange(self):
        if self.running == 1:
            self.xmpp.sendControlMessage()
        else:
            return

    def makeFriend(self):
        self.xmpp.update_roster(str(self.add.Jid.text()),name = str(self.add.Name.text()), subscription = str(self.add.Subscription.text()))

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    profile = Profile()
    sys.exit(app.exec_())
