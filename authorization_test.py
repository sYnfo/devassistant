#!/usr/bin/python


import dbus
import os

import slip.dbus.service

from slip.dbus import polkit

class DBusAuthentication(object):
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.dbus_object = self.bus.get_object("org.fedoraproject.devassistant.mechanishm",
                "/org/fedoraproject/devassistant/object")

    @polkit.enable_proxy
    def read(self):
        return self.dbus_object.read(dbus_interface="org.fedoraproject.devassistant.mechanishm")

    @polkit.enable_proxy
    def write(self, config_data):
        return self.dbus_object.write(config_data,
                dbus_interface="org.fedoraproject.devassistant.mechanishm")

example_object = DBusAuthentication()

example_object.write("myphp")
config_data = example_object.read()

print "config_data read successfully:"
print config_data

print "attempting to write config data"


