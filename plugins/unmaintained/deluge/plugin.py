# AwnDeluge

import dbus

class plugin_AwnDeluge: 
    def cargarAWN(self):
        global awn_ok
        awn_ok = False
        bus = dbus.SessionBus()
        try:
            obj = bus.get_object("com.google.code.Awn", "/com/google/code/Awn")
            awn_ok = True
        except dbus.DBusException:
            awn_ok = False
        if awn_ok:    
            global awn
            awn = dbus.Interface(obj, "com.google.code.Awn")  
            
    def __init__(self, path, deluge_core, deluge_interface):
        print "Loading AwnDeluge plugin..."
        self.path = path
        self.core = deluge_core
        self.interface = deluge_interface 
        self.cargarAWN()
           
    def unload(self):
        if awn_ok:
            awn.UnsetInfoByName("deluge")
        print "Unloading AwnDeluge plugin..."
                
    def update(self):
        global awn_ok
        if awn_ok:
            session_info = self.core.get_state()
            downRate=str(round(session_info['download_rate']/1024,1))     
            upRate=str(round(session_info['upload_rate']/1024,1))     
            try:
                awn.SetInfoByName("deluge",downRate + '-' + upRate)
            except dbus.DBusException:
                awn_ok = False
        else:
            self.cargarAWN()
        