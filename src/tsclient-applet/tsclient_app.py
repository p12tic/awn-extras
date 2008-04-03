#!/usr/bin/python

# File matching and folder listing
import os, glob

# GUI
import gtk

# AWN
import AWNLib

class TSClient:
    def __init__ (self, awnd, orient, height)
        self.awn = awn
        self.awn.icon.file("icons/Tsclient.svg")

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
        os.system('tsclient -x ' + rdpFile)
        #print rdpFile
        #print "hide title"

if __name__ == "__main__":
    awn = AWNLib.initiate({"name": "TSClient Applet",
        "short": "tsclient",
        "description": "Interact with the Terminal Services Client",
        "type": ["Utility", "RemoteAccess"]})
    applet = TSClientApplet(awn)
    AWNLib.start(applet.awn)
