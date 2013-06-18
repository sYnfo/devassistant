#!/usr/bin/python


import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import os

import slip.dbus.service

class DBusObject(slip.dbus.service.Object):

    def __init__(self, *p, **k):
        super(DBusObject, self).__init__(*p, **k)
        self.config_data = """These are the contents of a configuration file.

They extend over some lines. DevAssistant

And one more."""
        print "service object constructed"

    def __del__(self):
        print "service object deleted"

    @slip.dbus.polkit.require_auth("org.fedoraproject.devassistant.read")
    @dbus.service.method("org.fedoraproject.devassistant.mechanishm",
            in_signature="", out_signature="s")
    def read(self):
        print "%s.read() -> '%s'" %(self, self.config_data)
        return self.config_data

    @slip.dbus.polkit.require_auth("org.fedoraproject.devassistant.write")
    @dbus.service.method("org.fedoraproject.devassistant.mechanishm",
            in_signature="s", out_signature="")
    def write(self,config_data):
        print "%s.write() -> '%s'" %(self, config_data)
        self.config_data = config_data

if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    name = dbus.service.BusName("org.fedoraproject.devassistant.mechanishm",
            bus)
    object = DBusObject(name, "/org/fedoraproject/devassistant/object")
    mainloop = gobject.MainLoop()
    slip.dbus.service.set_mainloop(mainloop)
    print "Running dbus devassistant service"
    mainloop.run()
