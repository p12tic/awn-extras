#!/usr/bin/python

# File matching and folder listing
import glob
import os

# GUI
import gtk

# AWN
from awn.extras import AWNLib

#Running tsclient
import subprocess

applet_name = "TSClient Applet"
applet_version = "0.2.8"
applet_description = "Interact with the Terminal Services Client"

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "icons/tsclient-applet.svg")


class TSClient:
    def __init__ (self, awn):
        self.awn = awn
        self.awn.icon.theme("tsclient-applet")

        self.dialog = self.awn.dialog.new("main")

        a = glob.glob(os.path.expanduser("~/.tsclient/*.rdp"))
        for item in a:
            shortname, extension = os.path.splitext(os.path.split(item)[1])
            button = gtk.Button(label=shortname)
            self.dialog.add(button)
            button.show_all()
            button.connect("button-press-event", self.start_tsclient, item)
        button = gtk.Button(label="New Connection...")
        self.dialog.add(button)
        button.show_all()
        button.connect("button-press-event", self.start_tsclient, "")

    def start_tsclient (self, widget, event, rdpFile):
        subprocess.Popen('tsclient -x ' + rdpFile, shell=True)
        #print rdpFile
        #print "hide title"

if __name__ == "__main__":
    awn = AWNLib.initiate({"name": applet_name, "short": "tsclient-app",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "chimby",
        "copyright-year": 2007,
        "type": ["Utility", "RemoteAccess"]})
    applet = TSClient(awn)
    AWNLib.start(applet.awn)
