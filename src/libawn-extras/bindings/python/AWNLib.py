#!/usr/bin/python
#
#       AWN Applet Library
#
#       Copyright 2007 Pavel Panchekha <pavpanchekha@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import sys, os
import gobject
import gtk
from gtk import gdk
import awn
import StringIO
import types
import cPickle as cpickle
try:
    import awn.extras as extras
except:
    pass

___file___ = sys.argv[0] # Voodoo
# Basically, __file__ = current file location
# sys.argv[0] = file name or called file
# Since AWNLib is in site-packages, __file__ refers to something there
# For relative paths to work, we need a way of determining where the
# User applet is. So this bit of magic works

class KeyRingError: pass

class Dialogs:
    def __init__(self, parent, mainDlog=None, secDlog=None, program=None, context=None):
        self.main = mainDlog
        self.secondary = secDlog
        self.program = program
        self.menu = context
        self.parent = parent

    def register(self, dlog, type="main", focus=True):
        assert type in ["main", "secondary", "program", "menu"]
        self.__dict__[type] = dlog
        if focus and type != "program":
            dlog.connect("focus-out-event", lambda x, y: dlog.hide())

    def toggle(self, w=None, e=None):
        self.parent.title.show(show=False)

        if e.button == 3 and self.menu: # right click
            self.contextFocus(w, e)
        elif e.button == 2 and self.secondary: # middle click
            self.secondaryFocus(w, e) # other, including single click
        elif self.main:
            self.mainFocus(w, e)


    def new(self, type=None, focus=True):
        dlog = awn.AppletDialog(self.parent)
        if type != None:
            self.register(dlog, type, focus)
        return dlog

    def mainFocus(self, w=None, e=None):
        self.hide(self.secondary)
        self.hide(self.menu)
        if self.main.is_active():
            self.main.hide()
        else:
            self.main.show_all()

    def secondaryFocus(self, w=None, e=None):
        self.hide(self.main)
        self.hide(self.menu)
        if self.secondary:
            if self.secondary.is_active():
                self.secondary.hide()
            else:
                self.secondary.show_all()
        else:
            self.program()

    def contextFocus(self, w=None, e=None):
        self.hide(self.secondary)
        self.hide(self.main)
        self.menu.popup(None, None, None, e.button, e.time)

    def hide(self, x):
        try:
            x.hide()
        except:
            pass

class Title:
    def __init__(self, parent, text=None):
        self.__title = awn.awn_title_get_default()
        self.parent = parent
        if not text:
            text = self.parent.meta.info["name"]
        self.text = text

    def show(self, x=None, y=None, show=True):
        def f(text):
            if show:
                self.__title.show(self.parent, text)
            else:
                self.__title.hide(self.parent)

        f(self.text)

    def set(self, text=""):
        self.text = text

class Icon:
    def __init__(self, parent):
        self.parent = parent
        self.height = self.parent.height

    def getFile(self, file):
        return gdk.pixbuf_new_from_file(os.path.join(os.path.abspath( \
            os.path.dirname(___file___)), file)) # That voodoo up above?

    def getTheme(self, name):
        self.theme = gtk.IconTheme()
        return self.theme.load_icon (name, self.height, 0)


    def set(self, icon):
        if self.height != icon.get_height():
            icon = icon.scale_simple(self.height, \
                self.height, gtk.gdk.INTERP_BILINEAR)
        self.parent.set_temp_icon(icon)

    def surfaceToPixbuf(self, surface):
        sio = StringIO()
        surface.write_to_png(sio)
        sio.seek(0)
        loader = gtk.gdk.PixbufLoader()
        loader.write(sio.getvalue())
        loader.close()
        return loader.get_pixbuf()

class Modules:
    def __init__(self, parent):
        self.parent = parent

    def getmod(self, name):
        try:
            module = __import__(name)
        except ImportError:
            return False
        else:
            return module

    def depend(self, name, packagelist, callback):
        self.parent.dialog.new("main")

        # Table based layout
        table = gtk.Table()
        dlog.add(table)
        table.resize(3, 1)
        table.show_all()

        # Title of Window
        title = gtk.Label("<b>Error in %s:</b>" % self.parent.meta.info["name"])
        table.attach(title, 0, 1, 0, 1)
        title.set_use_markup(True)
        title.show_all()

        error = "You must have the program <i>%s</i> installed to use %s. \
        Make sure you do and click OK.\nHere is a list of distros and the \
         package names for each:\n\n" % (name, self.parent.meta.info["name"])
        for (k, v) in packagelist.items():
            error = "%s%s: <i>%s</i>\n" % (error, k, v)

        # Error Message
        text = gtk.Label(error)
        text.set_line_wrap(True)
        table.attach(text, 0, 1, 1, 2)
        text.set_use_markup(True)
        text.set_justify(gtk.JUSTIFY_FILL)
        text.show_all()

        # Submit button
        ok = gtk.Button(label = "OK, I've installed it")
        table.attach(ok, 0, 1, 2, 3)
        ok.show_all()

        def qu(x):
            dlog.hide()
            callback()

        ok.connect("clicked", qu)
        dlog.show_all()

    def get(self, name, packagelist, callback):
        module = self.getmod(name)
        if module:
            return callback(module)

        dlog = self.parent.dialog.new("main")

        # Table based layout
        table = gtk.Table()
        dlog.add(table)
        table.resize(3, 1)
        table.show_all()

        # Title of Window
        title = gtk.Label("<b>Error in %s:</b>" % self.parent.meta.info["name"])
        table.attach(title, 0, 1, 0, 1)
        title.set_use_markup(True)
        title.show_all()

        error = "You must have the python module <i>%s</i> installed to use %s. \
        Make sure you do and click OK.\nHere is a list of distros and the \
        package names for each:\n\n" % (name, self.parent.meta.info["name"])
        for (k, v) in packagelist.items():
            error = "%s%s: <i>%s</i>\n" % (error, k, v)

        # Error Message
        text = gtk.Label(error)
        text.set_line_wrap(True)
        table.attach(text, 0, 1, 1, 2)
        text.set_use_markup(True)
        text.set_justify(gtk.JUSTIFY_FILL)
        text.show_all()

        # Submit button
        ok = gtk.Button(label = "OK, I've installed it")
        table.attach(ok, 0, 1, 2, 3)
        ok.show_all()

        def qu(x):
            dlog.hide()
            self.get(name, packagelist)

        ok.connect("clicked", qu)
        dlog.show_all()

class Settings:
    def __init__(self, parent):
        self.parent = parent

    def require(self, folder=None):
        if not folder:
            folder = self.parent.meta.info["short"]
        if hasattr(awn, "Config"):
            self.client = self.AWNConfigUser(folder, self.parent)
        else:
            self.client = self.GConfUser(folder, self.parent)
        self.folder(folder)

    def folder(self, folder):
        self.client.update(folder)

    def notify(self, key, callback):
        self.client.notify(callback)

    def set(self, key, value, type="string"):
        try:
            self.get(key)
            self.client.set(key, value)
        except:
            self.new(key, value, type)

    def get(self, key):
        v = self.client.get(key)
        if type(v) == types.StringType and v[:9] == "!pickle;\n":
            v = cpickle.loads(v[9:])
        return v

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        tlist = {types.BooleanType: "bool",
                 types.IntType: "int",
                 types.LongType: "int",
                 types.FloatType: "float",
                 types.StringType: "string",
                }
        if type(value) in tlist.keys():
            t = tlist[type(value)]
        else:
            value = "!pickle;\n%s" % cpickle.dumps(value)
            t = "string"
        self.set(key, value, t)

    def __delitem__(self, name):
        self.delete(key)

    def new(self, key, value, type):
        self.client.new(key, value, type)

    def delete(self, key):
        self.client.delete(key)

    class GConfUser:
        def __init__(self, folder, parent):
            self.parent = parent
            self.update(folder)
            self.parent.module.get("gconf", {"Ubuntu": "python-gconf"}, self.init2)

        def init2(self, module):
            self.client = module.client_get_default()

        def update(self, folder):
            self.folder = folder

        def notify(self, key, callback):
            self.client.notify_add(self.folder, key, callback)

        def set(self, key, value):
            a = self.client.set_value(os.path.join(self.folder, key), value)

        def new(self, key, value, type):
            func = getattr(self.client, "set_%s" % type)
            func(os.path.join(self.folder, key), value)

        def get(self, key):
            return self.client.get_value(os.path.join(self.folder, key))

        def delete(self, key):
            self.client.unset(os.path.join(self.folder, key))

    class AWNConfigUser:
        def __init__(self, folder, parent):
            self.parent = parent
            self.update(folder)
            self.client = awn.Config()

        def update(self, folder):
            self.folder = os.path.join("applets", folder)

        def notify(self, key, callback):
            self.client.notify_add(self.folder, callback)

        def set(self, key, value):
            f = getattr(self.client, "set_%s" % self.type(key))
            f(self.folder, key, value)

        def new(self, key, value, type):
            func = getattr(self.client, "set_%s" % type)
            func(self.folder, key, value)

        def get(self, key):
            f = getattr(self.client, "get_%s" % self.type(key))
            return f(self.folder, key)

        def delete(self, key):
            self.client.unset(os.path.join(self.folder, key))

        def type(self, key):
            return self.client.get_value_type(self.folder, key).value_nick

class KeyRing:
    def __init__(self, parent):
        self.parent = parent

    def require(self):
        self.parent.module.get("gnomekeyring", {"Ubuntu": "gnome-keyring"}, self.require2)

    def require2(self, keyring):
        self.keyring = keyring
        if not self.keyring.is_available():
            raise KeyRingError
        keyring_list = self.keyring.list_keyring_names_sync()
        if len(keyring_list) == 0:
            raise KeyRingError
        self.ring = self.keyring.get_default_keyring_sync()

    def new(self, name=None, pwd=None, attrs={}, type="generic"):
        k = self.Key(self.keyring)
        if name and pwd:
            k.set(name, pwd, attrs, type)
        return k

    class Key(object):
        def __init__(self, keyring, token=0):
            self.keyring = keyring
            self.token = token

        def set(self, name, pwd, attrs={}, type="generic"):
            if type == "network":
                type = self.keyring.ITEM_NETWORK_PASSWORD
            elif type == "note":
                type = self.keyring.ITEM_NOTE
            else: # Generic included
                type = self.keyring.ITEM_GENERIC_SECRET

            self.token = self.keyring.item_create_sync(None, type, name, attrs, pwd, True)

        def get(self):
            return self.keyring.item_get_info_sync(None, self.token)

        def getAttrs(self):
            return keyring.item_get_attributes_sync(None, self.token)

        def setAttrs(self, a):
            return keyring.item_set_attributes_sync(None, self.token, a)

        def getName(self):
            return self.get().get_display_name()

        def setName(self, name):
            self.get().set_display_name(name)

        def getPass(self):
            return self.get().get_secret()

        def setPass(self, passwd):
            self.get().set_secret(passwd)

        def delete(self):
            self.keyring.item_delete_sync(None, self.token)

        attrs = property(getAttrs, setAttrs)
        name = property(getName, setName)
        password = property(getPass, setPass)


class Timing:
    def __init__(self, parent):
        self.parent = parent

    def time(self, callback, sec):
        c = self.Callback(callback)
        gobject.timeout_add(int(sec*1000), c.run)
        return c

    class Callback:
        def __init__(self, callback):
            self.callValue = True
            self.callback = callback

        def run(self, x=None):
            if self.callValue:
                self.callback()
            else:
                return False

        def stop(self):
            self.callValue = False

class Notify:
    def __init__(self, parent):
        self.parent = parent

    def require(self):
        try:
            extras.notify_message
        except:
            pass
        else:
            return
        n = os.system("notify-send")
        if n != 256:
            self.parent.module.depend("notify-send", {"Ubuntu": "libnotify-bin"}, self.require)

    def send(self, subject=None, body="", icon=""):
        if not subject:
            subject = "Message From " + self.parent.meta.info["name"]
        try:
            extras.notify_message(subject, body, icon, 0, 1)
        except:
            pass
        else:
            return

        os.system("notify-send %s \"%s\"" % (subject, body.replace("\"", "\\\"")))

class Effects:
    def __init__(self, parent):
        self.parent = parent
        self.effects = self.parent.get_effects()

    def notify(self):
        awn.awn_effect_start_ex(self.effects, "attention", 0, 0, 1)

    def launch(self):
        awn.awn_effect_start_ex(self.effects, "launching", 0, 0, 1)

class Meta:
    def __init__(self, parent, info={}):
        self.parent = parent
        self.info = {
                     "name": "Applet",
                     "short": "applet",
                     }
        for (k, v) in info.items():
            self.info[k] = v

    def update(self, info):
        for (k, v) in info.items():
            self.info[k] = v

class App(awn.AppletSimple):
    def __init__(self, uid, orient, height, meta={}):
        awn.AppletSimple.__init__(self, uid, orient, height)
        self.height = height
        self.uid = uid
        self.orient = orient

        self.meta = Meta(self, meta)

        self.icon = Icon(self)
        self.dialog = Dialogs(self)
        self.title = Title(self)
        self.module = Modules(self)
        self.settings = Settings(self)
        self.timing = Timing(self)
        self.keyring = KeyRing(self)
        self.notify = Notify(self)
        self.effects = Effects(self)

        self.connect("button-press-event", self.dialog.toggle)
        self.connect("enter-notify-event", self.title.show)
        self.connect("leave-notify-event", lambda x, y: self.title.show(show=False))

def initiate(info={}):
    awn.init(sys.argv[1:])
    applet = App(awn.uid, awn.orient, awn.height, meta=info)
    awn.init_applet(applet)
    return applet

def start(applet):
    applet.show_all()
    gtk.main()
