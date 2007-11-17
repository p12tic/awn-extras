# !/usr/bin/python

import sys, os
import gobject
import dbus
import gconf
from dbus.mainloop.glib import DBusGMainLoop

class Notif:
    service = {"service_name":"org.freedesktop.Notifications",
               "object_path":"/org/freedesktop/Notifications",
               "interface":"org.freedesktop.Notifications"}
    session_bus = dbus.SessionBus()
    proxy_obj = session_bus.get_object(service['service_name'],
                                       service['object_path'])
    dbus_int = dbus.Interface(proxy_obj, service['interface'])
    
def send(app_name = "None" , replaces_id = 0, icon = "",
         title = "", body = "", actions = [], hints = {}, timeout = 9000):
    """
    A simple method that 
    
    A call of notif.send(title="some text") will display a notification 
    with just a title. All the arguments are optional.
    
    title is the title of the notification
    body is the notification's body
    timeout is the time until the notification goes away
    icon is the icon path
    """
    app_name = dbus.String(app_name)
    replaces_id = dbus.UInt32(replaces_id)
    icon = dbus.String(icon)
    title = dbus.String(title)
    body = dbus.String(body)
    actions = dbus.Array(actions)
    timeout = dbus.Int32(timeout)
    data.dbus_int.Notify(app_name,replaces_id,icon,title,
                         body,actions,hints,timeout)

def send_advanced(app_name = "None" , replaces_id = 0,
                  icon = "", title = "", body = "", actions = [],
                  hints = {}, timeout = 9000, properties=None):
    """
    the properties argument is a list containing any properties you
    would like to pass to the notification daemon 
    
    Refer to the send function's documentation for more info
    """
    app_name = dbus.String(app_name)
    replaces_id = dbus.UInt32(replaces_id)
    icon = dbus.String(icon)
    title = dbus.String(title)
    if properties != None:
        for item in properties:
            body = body + "$||@" + item + "@||$"
    print body
    body = dbus.String(body)
    actions = dbus.Array(actions)
    timeout = dbus.Int32(timeout)
    data.dbus_int.Notify(app_name, replaces_id, icon, title,
                         body, actions, hints, timeout)
#####
data = Notif()
