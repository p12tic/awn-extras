#!/usr/bin/python
#
#       AWN Applet Library - simplifies the API's used in programming applets
#       for AWN.
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

# Path manipulations and file name
import sys, os, subprocess

# GUI drawing and timers
import gobject, gtk

# For type checking for gconf/settings
import types

# For object serialization into gconf
import cPickle as cpickle

# For the raw AWN API
import awn

try:
    # The libawn-extras additions. Not always available
    import awn.extras as extras
except:
    # Use in surfaceToPixbuf
    import StringIO

    # To make tests easier later
    extras = None

___file___ = sys.argv[0]
# Basically, __file__ = current file location
# sys.argv[0] = file name or called file
# Since AWNLib is in site-packages, __file__ refers to something there
# For relative paths to work, we need a way of determining where the
# User applet is. So this bit of magic works.

class KeyRingError:
    def __init__(self, str):
        self.msg = str

    def __str__(self):
        return self.msg
# Stupid keyring has quite a few ways to go wrong.

class Dialogs:
    def __init__(self, parent):
        """
        Creates instance of Dialogs object

        @param parent: The parent applet of the dialogs instance.
        @type parent: L{Applet}
        """

        self.__register = {}
        self.__current = None

        self.__parent = parent


    def new(self, dialog, title=None, focus=True):
        """
        Create a new AWN dialog

        @param dialog: The name to register the dialog under.
        @type dialog: C{string}
        @param title: The title of the new dialog
        @type title: C{string}
        @param focus: Whether to force the focus
        @type focus: C{bool}
        @return: The new menu or dialog
        @rtype: C{gtk.Menu}, C{function}, or C{awn.AppletDialog}
        """

        if dialog == "menu":
            dlog = gtk.Menu()
        elif dialog == "program":
            dlog = lambda: None
        else:
            dlog = awn.AppletDialog(self.__parent)

        self.register(dialog, dlog)
        if focus and dialog not in ("program", "menu"):
            dlog.connect("focus-out-event", lambda x, y: dlog.hide())

        if dialog not in ("program", "menu") and title:
            dlog.set_title(title)

        return dlog

    def register(self, dialog, dlog):
        """
        Register a dialog to be used by AWNLib.

        @param dialog: The name to use for the dialog. The predefined values
                       are main, secondary, menu, and program.
        @type dialog: C{string}
        @param dlog: The actual dialog or menu or function.
        @type dlog: C{function}, C{gtk.Menu}, or C{awn.AppletDialog}
        """

        self.__register[dialog] = dlog

    def toggle(self, dialog, force="", once=False):
        """
        Shows a dialog.

        @param dialog: The dialog that should be shown.
        @type dialog: C{string}
        @param force: "Hide" or "Show". Whether to force the hiding or showing
                      of the dialog in question.
        @type force: C{string}
        @param once: Only show or hide one dialog. If a dialog is already
            opened, and you request that another dialog be toggled, only the
            open one is hidden. False by default.
        @type once: C{bool}
        """

        force = force.lower()
        assert force in ("hide", "show", ""), \
            "Force must be \"hide\", \"show\", or \"\""
        assert dialog in self.__register, \
            "Dialog must be registered"

        if self.__parent:
            self.__parent.title.hide()

        if dialog == "menu":
            self.__register["menu"].popup(None, None, None, e.button, e.time)
        elif dialog == "program":
            self.__register["program"]()
        else:
            if self.__register[dialog].is_active() or force == "hide" and \
                force != "show":
                self.__register[dialog].hide()
                self.__current = None
            else:
                if self.__current:
                    self.__current.hide()
                    if once:
                        self.__current = None
                        return

                self.__register[dialog].show_all()
                self.__current = self.__register[dialog]

    def hide(self):
        """
        Hide all dialogs.
        """

        if self.__current:
            self.__current.hide()
            self.__current = None

    def click(self, w=None, e=None):
        """
        Responds to click events. Only called by GTK.
        """

        if e.button == 3 and "menu" in self.__register: # Right click
            self.toggle("menu", once=True)
        elif e.button == 2 and "program" in self.__register: # Middle click
            self.toggle("program", once=True)
        elif e.button == 2 and "secondary" in self.__register: # Middle click
            self.toggle("secondary", once=True)
        elif e.button == 1 and "main" in self.__register:
            self.toggle("main", once=True)

class Title:
    def __init__(self, parent, text=None):
        """
        Creates a new Title object.

        @param parent: The parent applet of the title instance.
        @type parent: L{Applet}
        @param text: The text to fill the title with. Defaults to the meta name
                     property.
        @type text: C{string}
        """

        if not text:
            text = parent.meta["name"]

        self.__title = awn.awn_title_get_default()
        self.__parent = parent
        self.__text = text
        self.__showing = False

    def show(self, w=None, e=None):
        """
        Show the applet title.
        """

        self.__title.show(self.__parent, self.__text)
        self.__showing = True

    def hide(self, w=None, e=None):
        """
        Hides the applet title.
        """

        self.__title.hide(self.__parent)
        self.__showing = False

    def set(self, text=""):
        """
        Sets the applet title.

        @param text: The new title text. Defaults to "".
        @type text: C{string}
        """

        self.__text = text
        if self.__showing:
            self.show()

class Icon:
    def __init__(self, parent):
        """
        Creates a new Icon object.

        @param parent: The parent applet of the icon instance.
        @type parent: L{Applet}
        """

        self.__parent = parent
        self.__height = self.__parent.height

    def file(self, file, set=True):
        """
        Get an icon from a file location.

        @param file: The path to the file. Can be relative or absolute.
        @type file: C{string}
        @param set: Whether to also set the icon. True by default.
        @type set: C{bool}
        @return: The resultant pixbuf or None (if C{set} is C{True})
        @rtype: C{gtk.gdk.Pixbuf} or C{None}
        """

        if file[0] != "/":
            file = os.path.join(os.path.abspath( \
                os.path.dirname(___file___)), file)

        icon = gtk.gdk.pixbuf_new_from_file(file)

        if set:
            self.set(icon)
        else:
            return icon

    def theme(self, name, set=True):
        """
        Get an icon from the default icon theme.

        @param name: The name of the theme icon.
        @type name: C{string}
        @param set: Whether to also set the icon. True by default.
        @type set: C{bool}
        @return: The resultant pixbuf or None (if C{set} is C{True})
        @rtype: C{gtk.gdk.Pixbuf} or C{None}
        """

        self.theme = gtk.IconTheme()
        icon = self.theme.load_icon(name, self.height, 0)

        if set:
            self.set(icon)
        else:
            return icon

    def surface(self, surface, set=True):
        """
        Convert a C{cairo} surface to a C{gtk.gdk.Pixbuf}.

        @param surface: The C{cairo} surface to convert.
        @type surface: C{cairo.Surface}
        @param set: Whether to also set the icon. True by default.
        @type set: C{bool}
        @return: The resultant pixbuf or None (if C{set} is C{True})
        @rtype: C{gtk.gdk.Pixbuf} or C{None}
        """

        if extras:
            icon = extras.surface_to_pixbuf(surface)
        else:
            sio = StringIO()
            surface.write_to_png(sio)
            sio.seek(0)
            loader = gtk.gdk.PixbufLoader()
            loader.write(sio.getvalue())
            loader.close()
            icon = loader.get_pixbuf()

        if set:
            self.set(icon)
        else:
            return icon

    def set(self, icon, raw=False):
        """
        Set a C{gtk.gdk.pixbuf} as your applet icon.

        @param icon: The icon to set your applet icon to.
        @type icon: C{gtk.gdk.Pixbuf}
        @param raw: If true, don't resize the passed pixbuf. False by default.
        @type raw: C{bool}
        """

        if not raw:
            h = icon.get_height() # To resize non-square icons.
            h2 = self.__height
            w = icon.get_width()
            w2 = int((1.0*h2)/h*w)

            if h2 != h:
                icon = icon.scale_simple(w2, h2, gtk.gdk.INTERP_BILINEAR)
        self.__parent.set_temp_icon(icon)
        self.__parent.show()

    def hide(self):
        """
        Hide the applet's icon.
        """

        self.__parent.hide()

class Modules:
    def __init__(self, parent):
        """
        Creates a new Modules object.

        @param parent: The parent applet of the icon instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

    def depend(self, name, packagelist, callback):
        """
        Tells the user that they need to install a program to use your applet.
        Note that this does not do any checking to determine whether the
        said program is installed. You must do all checking yourself.

        @param name: the name of the program that must be installed.
        @type name: C{string}
        @param packagelist: A dict of "distro": "package" pairs with the names
            of the packages of the given distro that can be used to install the
            said program.
        @type packagelist: C{dict}
        @param callback: The function to be called when the user claims to have
            installed the necessary program. Remember that you must check
            whether or not this is true.
        @type callback: C{function}
        """

        dlog = self.__parent.dialog.new("main")

        dlog = self.__parent.dialog.new("main")
        dlog.set_title("<b>Error in %s:</b>" % self.__parent.meta["name"])
        vbox = gtk.VBox()

        error = "You must have the program <i>%s</i> installed to use %s. \
        Make sure you do and click OK.\nHere is a list of distros and the \
         package names for each:\n\n" % (name, self.__parent.meta["name"])
        for (k, v) in packagelist.items():
            error = "%s%s: <i>%s</i>\n" % (error, k, v)

        # Error Message
        text = gtk.Label(error)
        text.set_line_wrap(True)
        text.set_use_markup(True)
        text.set_justify(gtk.JUSTIFY_FILL)
        vbox.pack_start(text)

        # Submit button
        ok = gtk.Button(label = "OK, I've installed it")
        ok.show_all()
        vbox.pack_start(text)

        def qu(x):
            dlog.hide()
            callback()

        ok.connect("clicked", qu)
        dlog.show_all()

    def get(self, name, packagelist, callback):
        """
        Tells the user that they need to install a module to use your applet.
        This function will attempts to import the module, and if this is not
        possible, alert the user. Otherwise, it will call your callback with
        the module as the first (and only) argument

        @param name: the name of the module that must be installed.
        @type name: C{string}
        @param packagelist: A dict of "distro": "package" pairs with the names
            of the packages of the given distro that can be used to install the
            said module.
        @type packagelist: C{dict}
        @param callback: The function to be called when the user claims to have
            installed the necessary module. The module is passed as the first
            and only argument to the callback.
        @type callback: C{function}
        @return: The module requested.
        @rtype: C{module}
        """

        try:
            module = __import__(name)
        except ImportError:
            module = False

        if module:
            return callback(module)

        dlog = self.__parent.dialog.new("main")
        dlog.set_title("<b>Error in %s:</b>" % self.__parent.meta["name"])
        vbox = gtk.VBox()

        error = "You must have the python module <i>%s</i> installed to use %s. \
        Make sure you do and click OK.\nHere is a list of distros and the \
        package names for each:\n\n" % (name, self.__parent.meta["name"])
        for (k, v) in packagelist.items():
            error = "%s%s: <i>%s</i>\n" % (error, k, v)

        # Error Message
        text = gtk.Label(error)
        text.set_line_wrap(True)
        text.set_use_markup(True)
        text.set_justify(gtk.JUSTIFY_FILL)
        vbox.pack_start(text)

        # Submit button
        ok = gtk.Button(label = "OK, I've installed it")
        ok.show_all()
        vbox.pack_start(text)

        def qu(x):
            dlog.hide()
            self.get(name, packagelist, callback)

        ok.connect("clicked", qu)
        dlog.show_all()

class Settings:
    def __init__(self, parent):
        """
        Creates a new Settings object. Note that the Settings object should be
        used as a dictionary.

        @param parent: The parent applet of the settings instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

    def require(self, folder=None):
        """
        Imports necessary modules. Should be called before any other functions
        are used. Should only be called if the applet expects to use Settings.

        @param folder: The folder to use for your applet. If not given, the
            "short" meta information is used.
        @type folder: C{string}
        """

        if not folder:
            folder = self.__parent.meta["short"]

        if hasattr(awn, "Config"):
            self.client = self.AWNConfigUser(folder)
        else:
            self.client = self.GConfUser(folder)
            self.__parent.module.get("gconf", { \
                "Debian/Ubuntu": "python-gconf", \
                "Gentoo": "dev-python/gnome-python", \
                "OpenSUSE": "python-gnome"}, self.client.load)

        self.cd(folder)

    def cd(self, folder):
        """
        Change to another folder. Note that this will change folders to e.g.
        /apps/avant-window-navigator/applets/[folder] in the GConf
        implementation and to just /applets/[folder] in the iniKey
        implementation.

        @param folder: The folder to use for your applet. If not given, the
            "short" meta information is used.
        @type folder: C{string}
        """

        if not folder:
            folder = self.__parent.meta["short"]

        self.client.cd(folder)

    def notify(self, key, callback):
        """
        Set up a function to be executed every time a key changes. Note that
        this works best (if at all) on whole folders, not individual keys.

        @param key: The key or folder to monitor for changes.
        @type key: C{string}
        @param callback: The function to call upon changes.
        @type callback: C{function}
        """

        self.client.notify(key, callback)

    def __set(self, key, value, type="string"):
        try:
            self.client.set(key, value)
        except ValueError, AttributeError:
            self.client.new(key, value, type)

    def __get(self, key):
        v = self.client.get(key)
        if type(v) == types.StringType and v[:9] == "!pickle;\n":
            v = cpickle.loads(v[9:])
        return v

    def __getitem__(self, key):
        """
        Get a key from the currect directory.

        @param key: A relative path to the correct key
        @type key: C{string}
        @return: The value of the key
        @rtype: C{object}
        """

        return self.__get(key)

    def __setitem__(self, key, value):
        """
        Set or create a key from the currect directory.

        @param key: A relative path to the correct key
        @type key: C{string}
        """
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
        self.__set(key, value, t)

    def __delitem__(self, key):
        """
        Delete a key from the currect directory.

        @param key: A relative path to the correct key
        @type key: C{string}
        """

        self.client.delete(key)

    class GConfUser:
        def __init__(self, folder):
            """
            Creates a new GConfUser.

            @param folder: Folder to start with. /apps/avant-window-navigator \
            /applets is prepended to the folder name. To change to a folder
            without that prepended, pass the raw=True parameter to cd().
            @type folder: C{string}
            """

            self.cd(folder)

        def load(self, module):
            """
            Loads the gconf module to allow the GConfUser object to actually
            work.

            @param module: the gconf module.
            @type module: C{module}
            """

            self.__client = module.client_get_default()

        def cd(self, folder, raw=False):
            """
            Change the current directory. If the C{raw} parameter if False,
            "/apps/avant-window-navigator/applets" is prepended to C{folder}.

            @param folder: the folder to change into
            @type folder: C{string}
            @param raw: If False, "/apps/avant-window-navigator/applets" \
                is prepended to C{folder}.
            @type raw: C{bool}
            """

            if not raw:
                folder = os.path.join("/apps/avant-window-navigator/applets", \
                    folder)

            self.__folder = folder

        def notify(self, key, callback):
            """
            Set up a function to be executed every time a key changes. Works
            best (if at all) on whole folders, not individual keys.

            @param key: The key or folder to monitor for changes.
            @type key: C{string}
            @param callback: The function to call upon changes.
            @type callback: C{function}
            """

            self.__client.notify_add(self.__folder, key, callback)

        def set(self, key, value):
            """
            Set an existing key's value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @param value: The value to set the key to.
            @type value: C{bool}, C{int}, C{float}, or C{string}
            """

            a = self.__client.set_value(os.path.join(self.__folder, key) \
                , value)

        def new(self, key, value, type):
            """
            Create a new key and set its value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @param value: The value to set the key to.
            @type value: C{bool}, C{int}, C{float}, or C{string}
            @param type: The type to make the new key.
            @type type: C{string}; "bool", "int", "float", or "string"
            """

            func = getattr(self.__client, "set_%s" % type)
            func(os.path.join(self.__folder, key), value)

        def get(self, key):
            """
            Get an existing key's value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @return: The value of the key
            @rtype: C{object}
            """

            return self.__client.get_value(os.path.join(self.__folder, key))

        def delete(self, key):
            """
            Delete an existing key.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            """

            self.__client.unset(os.path.join(self.__folder, key))

        def type(self, key):
            """
            Get an existing key's type.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @return: The type of the key.
            @rtype: C{string}
            """

            return self.__client(os.path.join(self.__folder, key)).type \
                .value_nick

    class AWNConfigUser:
        def __init__(self, folder):
            """
            Creates a new GConfUser.

            @param folder: Folder to start with. /applets is prepended to the
                folder name. To change to a folder without that prepended, pass
                the raw=True parameter to cd().
            @type folder: C{string}
            """

            self.cd(folder)
            self.__client = awn.Config()

        def cd(self, folder, raw=False):
            """
            Change the current directory. If the C{raw} parameter if False,
            "/applets" is prepended to C{folder}.

            @param folder: The folder to change into.
            @type folder: C{string}
            @param raw: If False, "/applets" is prepended to C{folder}.
            @type raw: C{bool}
            """

            if not raw:
                folder = os.path.join("applets", folder)

            self.__folder = folder

        def notify(self, key, callback):
            """
            Set up a function to be executed every time a key changes. Works
            best (if at all) on whole folders, not individual keys.

            @param key: The key or folder to monitor for changes.
            @type key: C{string}
            @param callback: The function to call upon changes.
            @type callback: C{function}
            """

            self.__client.notify_add(self.__folder, callback)

        def set(self, key, value):
            """
            Set an existing key's value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @param value: The value to set the key to.
            @type value: C{bool}, C{int}, C{float}, or C{string}
            """

            try:
                f = getattr(self.__client, "set_%s" % self.type(key))
            except:
                raise ValueError
            f(self.__folder, key, value)

        def new(self, key, value, type):
            """
            Create a new key and set its value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @param value: The value to set the key to.
            @type value: C{bool}, C{int}, C{float}, or C{string}
            @param type: The type to make the new key.
            @type type: C{string}; "bool", "int", "float", or "string"
            """

            func = getattr(self.__client, "set_%s" % type)
            func(self.__folder, key, value)

        def get(self, key):
            """
            Get an existing key's value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @return: The value of the key
            @rtype: C{object}
            """

            try:
                f = getattr(self.__client, "get_%s" % self.type(key))
            except:
                raise ValueError
            return f(self.__folder, key)

        def delete(self, key):
            """
            Delete an existing key. Not yet implemented; will raise the
            NotImplementedError. Will be implemented when implemented upstream.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            """

            raise NotImplementedError, "AWNConfig does not support deleting"

        def type(self, key):
            """
            Get an existing key's type.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @return: The type of the key
            @rtype: C{object}
            """

            return self.__client.get_value_type(self.__folder, key).value_nick

class KeyRing:
    def __init__(self, parent):
        """
        Creates a new Keyring object.

        @param parent: The parent applet of the keyring instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

    def require(self):
        """
        Imports necessary modules. Should be called before any other functions
        are used. Should only be called if the applet expects to use KeyRing.
        """

        self.__parent.module.get("gnomekeyring", { \
            "Debian/Ubuntu": "gnome-keyring", \
            "Gentoo": "gnome-base/gnome-keyring", \
            "OpenSUSE": "gnome-keyring"}, self.__require2)

    def __require2(self, keyring):
        self.__keyring = keyring

        if not self.__keyring.is_available():
            raise KeyRingError, "Keyring not available"

        keyring_list = self.__keyring.list_keyring_names_sync()

        if len(keyring_list) == 0:
            raise KeyRingError, "No keyrings available"
        try:
            self.__keyring.get_default_keyring_sync()
        except __keyring.NoKeyringDaemonError:
            raise KeyRingError, "Had trouble connecting to daemon"

    def new(self, name=None, pwd=None, attrs={}, type="generic"):
        """
        Create a new keyring key.

        @param name: The display name of the key. If omitted, an empty key is
            returned.
        @type name: C{string}
        @param pwd: The password stored in the key. If omitted, an empty key is
            returned.
        @type pwd: C{string}
        @param attrs: Other attributes stored in the key. By default: {}
        @type attrs: C{dict}
        @param type: The type of key. By default: "generic"
        @type type: C{string}; "generic", "network", or "note"
        @return: A new L{Key} object
        @rtype: L{Key}
        """

        k = self.Key(self.__keyring)
        if name and pwd:
            k.set(name, pwd, attrs, type)
        return k

    def fromToken(self, token):
        """
        Load the key with the given token.

        @param token: The password token of the key
        @type token: C{int} or C{long}
        @return: A new L{Key} object
        @rtype: L{Key}
        """

        k = self.Key(self.__keyring)
        k.token = token
        return k

    class Key(object):
        def __init__(self, keyring, token=0):
            """
            Create a new key.

            @param keyring: The keyring module.
            @type keyring: C{module}
            @param token: The token of an already-existing key. Optional.
            @type token: C{long}
            """

            self.__keyring = keyring
            self.token = token

        def set(self, name, pwd, attrs={}, type="generic"):
            """
            Create a new keyring key. Note that if another key exists with the
            same name, it will be overwritten.

            @param name: The display name of the key.
            @type name: C{string}
            @param pwd: The password stored in the key.
            @type pwd: C{string}
            @param attrs: Other attributes stored in the key. By default: {}
            @type attrs: C{dict}
            @param type: The type of key. By default: "generic"
            @type type: C{string}; "generic", "network", or "note"
            """

            if type == "network":
                type = self.__keyring.ITEM_NETWORK_PASSWORD
            elif type == "note":
                type = self.__keyring.ITEM_NOTE
            else: # Generic included
                type = self.__keyring.ITEM_GENERIC_SECRET

            self.token = self.__keyring.item_create_sync(None, type, name, \
                attrs, pwd, True)

        def delete(self):
            """
            Delete the current key. Will also reset the token. Note that
            "del [Key]" will not delete the key itself; that would be too
            destructive. delete() MUST be called manually.
            """

            self.__keyring.item_delete_sync(None, self.token)
            self.token = 0

        def __get(self):
            return self.__keyring.item_get_info_sync(None, self.token)

        def __getAttrs(self):
            return self.__keyring.item_get_attributes_sync(None, self.token)

        def __setAttrs(self, a):
            return self.__keyring.item_set_attributes_sync(None, self.token, a)

        def __getName(self):
            return self.__get().get_display_name()

        def __setName(self, name):
            self.__get().set_display_name(name)

        def __getPass(self):
            return self.__get().get_secret()

        def __setPass(self, passwd):
            self.__get().set_secret(passwd)

        attrs = property(__getAttrs, __setAttrs)
        """
        @ivar: The other attributes stored in the Key. Can be used like any
        property.
        """

        name = property(__getName, __setName)
        """
        @ivar: The display name of the Key. Can be used like any property
        """

        password = property(__getPass, __setPass)
        """
        @ivar: The password stored in the Key. Can be used like any property.
        """

class Timing:
    def __init__(self, parent):
        """
        Creates a new Timing object.

        @param parent: The parent applet of the timing instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

    def time(self, callback, sec):
        """
        Create a new timer-run function.

        @param callback: Function to be called.
        @type callback: C{function}
        @param sec: Number of seconds within each call.
        @type sec: C{float} or C{int}
        @return: A L{Callback} object for the C{callback} parameter
        @rtype: L{Callback}
        """

        c = self.Callback(callback)
        gobject.timeout_add(int(sec*1000), c.run)
        return c

    class Callback:
        def __init__(self, callback):
            """
            Creates a new Callback object.

            @param callback: The function to wrap the Callback around.
            @type callback: C{function}
            """

            self.__callValue = True
            self.__callback = callback

        def run(self, x=None, y=None):
            """
            The function to be called by the timer.
            """

            if self.__callValue:
                self.__callback()

            return self.__callValue

        def stop(self):
            """
            Stop the callback from ever running again.
            """

            self.__callValue = False

class Notify:
    def __init__(self, parent):
        """
        Creates a new Notify object.

        @param parent: The parent applet of the notify instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

    def require(self):
        """
        Imports necessary modules and checks for dependancies. Should be called
        before any other functions are used. Should only be called if the
        applet expects to use Notify.
        """

        if extras:
            return

        n = subprocess.call(["notify-send"])
        if n != 256:
            self.__parent.module.depend("notify-send", { \
                "Debian/Ubuntu": "libnotify-bin", \
                "Gentoo": "x11-libs/libnotify", \
                "OpenSUSE": "libnotify"}, self.require)

    def send(self, subject=None, body="", icon=""):
        """
        Sends a new libnotify message.

        @param subject: The subject of your message. If blank, "Message from
            [applet - full name]" is used.
        @type subject: C{string}
        @param body: The main body of your message. Blank by default.
        @type body: C{string}
        @param icon: The full absolute path to the name of the icon to use.
        @type icon: C{string}
        """

        if not subject:
            subject = "Message From " + self.__parent.meta["name"]

        if extras:
            extras.notify_message(subject, body, icon, 0, False)
            return

        body = '"' + body.replace("\"", "\\\"") + '"'
        icon = '"' + icon + '"'
        subprocess.call(["notify-send", subject, body, "-i", icon])

class Effects:
    def __init__(self, parent):
        """
        Creates a new Effects object.

        @param parent: The parent applet of the effects instance.
        @type parent: L{Applet}
        """

        self.__parent = parent
        self.__effects = self.__parent.get_effects()

    def notify(self):
        """
        Launches the notify effect. Should be used when the user's attention
        is required.
        """

        awn.awn_effect_start_ex(self.__effects, "attention", 0, 0, 1)

    def launch(self):
        """
        Launches the launch effect. Should be used when launching another
        program.
        """

        awn.awn_effect_start_ex(self.__effects, "launching", 0, 0, 1)

class Meta:
    def __init__(self, parent, info={}):
        """
        Creates a new Meta object.

        @param parent: The parent applet of the meta instance.
        @type parent: L{Applet}
        @param info: Default values for the meta dictionary
        @type info: C{dict}
        """

        self.__parent = parent
        self.__info = {
                     "name": "Applet",
                     "short": "applet",
                     }
        self.update(info)

    def update(self, info):
        """
        Updates the meta instance with new information

        @param info: Default values for the meta dictionary
        @type info: C{dict}
        """

        self.__info.update(info)

    def __getitem__(self, key):
        """
        Get a key from the dictionary

        @param key: The key
        @type key: C{string}
        """

        return self.__info[key]

    def __setitem__(self, key, value):
        """
        Set a key in the dictionary

        @param key: The key
        @type key: C{string}
        @param value: The value
        @type value: C{string}
        """
        self.__info[key] = value

    def __delitem__(self, key):
        """
        Delete a key from the dictionary

        @param key: The key
        @type key: C{string}
        """

        del self.__info[key]

class Applet(awn.AppletSimple):
    def __init__(self, uid, orient, height, meta={}):
        """
        Create a new instance of the Applet object.

        @param uid: The unique identifier of the applet
        @type uid: C{string}
        @param orient: The orientation of the applet. 0 means that the AWN bar
            is on the bottom of the screen.
        @type orient: C{int}
        @param height: The height of the applet.
        @type height: C{int}
        @param meta: The meta information to be passed to the Meta constructor
        @type meta: C{dict}
        """

        # Create a new applet
        awn.AppletSimple.__init__(self, uid, orient, height)

        # Store the values we were called with
        self.height = height
        self.uid = uid
        self.orient = orient

        # Create all the child-objects
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

        # Connect the necessary events to the sub-objects.
        self.connect("button-press-event", self.dialog.click)
        self.connect("enter-notify-event", self.title.show)
        self.connect("leave-notify-event", self.title.hide)

def initiate(meta={}):
    """
    Do the work to create a new applet. This does not yet run the applet.

    @param meta: The meta-information to pass to the constructor
    @type meta: C{dict}
    @return: The newly created applet.
    @rtype: L{Applet}
    """

    awn.init(sys.argv[1:]) # Initiate
    applet = Applet(awn.uid, awn.orient, awn.height, meta=meta) # Construct
    awn.init_applet(applet) # Add

    return applet

def start(applet):
    """
    Start the applet. This makes the icon appear on the bar and starts GTK+/

    @param applet: The applet to start.
    @type applet: L{Applet}
    """

    applet.show_all() # Show
    gtk.main() # Start
