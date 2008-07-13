#!/usr/bin/env python
#
#       AWN Applet Library - simplifies the API's used in programming applets
#       for AWN.
#
#       Copyright (C) 2007 - 2008 Pavel Panchekha <pavpanchekha@gmail.com>
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

import os
import subprocess
import sys

import gobject
import gtk

# For type checking for gconf/settings
import types

# For object serialization into gconf
import cPickle as cpickle

# For the raw AWN API
import awn

# For the Networking class
import urllib

import awn.extras as extras

___file___ = sys.argv[0]
# Basically, __file__ = current file location
# sys.argv[0] = file name or called file
# Since AWNLib is in site-packages, __file__ refers to something there
# For relative paths to work, we need a way of determining where the
# User applet is. So this bit of magic works.

_globalRegister = {}


class KeyRingError:
    def __init__(self, str):
        self.msg = str

    def __str__(self):
        return self.msg
# Stupid keyring has quite a few ways to go wrong.


class Dialogs:
    def __init__(self, parent):
        """
        Creates instance of Dialogs object. Will create a menu,
        an about dialog, and add that to the menu.

        @param parent: The parent applet of the dialogs instance.
        @type parent: L{Applet}
        """

        self.__register = {}
        self.__current = None
        self.__parent = parent

        self.__parent.settings.cd("shared")
        
        self.menu = self.new("menu")
        
        if "all" not in globals():
            def all(iterable):
                for element in iterable:
                    if not element:
                        return False
                return True
        
        meta_keys = self.__parent.meta.keys()

        # Create the About dialog if the applet provides the necessary metadata
        if all([key in meta_keys for key in ("name", "author", "copyright-year")]):
            about_dialog = self.new("about")

            about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
            self.menu.append(about_item)
            about_item.connect("activate", lambda w: self.toggle("about"))

        try:
            self.__loseFocus = self.__parent.settings["dialog_focus_loss_behavior"]
        except ValueError:
            self.__loseFocus = True

        self.__parent.settings.cd()

    def new(self, dialog, title=None, focus=True):
        """
        Create a new AWN dialog.

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
            dlog = self.__parent.create_default_menu()
            dlog.show_all()
        elif dialog == "program":
            dlog = lambda: None
        elif dialog == "about":
            dlog = self.AboutDialog(self.__parent)
        elif dialog == "preferences":
            dlog = self.PreferencesDialog(self.__parent)
            focus = False
        else:
            dlog = awn.AppletDialog(self.__parent)

        self.register(dialog, dlog, focus)

        if dialog not in ("program", "menu") and title:
            dlog.set_title(" " + title + " ")

        return dlog

    def register(self, dialog, dlog, focus=True):
        """
        Register a dialog to be used by AWNLib. 

        @param dialog: The name to use for the dialog. The predefined values
                       are main, secondary, menu, and program.
        @type dialog: C{string}
        @param dlog: The actual dialog or menu or function.
        @type dlog: C{function}, C{gtk.Menu}, or C{awn.AppletDialog}
        @param focus: Whether to bind focus in-out handlers for the dialog.
        @type focus: C{bool}
        """

        if focus and dialog not in ("program", "menu", "about") and self.__loseFocus:
            def hideDlog():
                self.__current = None
                dlog.hide()

            dlog.connect("focus-out-event", lambda x, y: hideDlog())

        self.__register[dialog] = dlog

    def toggle(self, dialog, force="", once=False, time=0):
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
        @param time: The time of the toggle. Usually taken from gtkEvent.time
        @type time: C{int}
        """

        force = force.lower()
        assert force in ("hide", "show", ""), \
            "Force must be \"hide\", \"show\", or \"\""
        assert dialog in self.__register, \
            "Dialog must be registered"

        if self.__parent:
            self.__parent.title.hide()

        if dialog == "menu":
            self.__register["menu"].show_all()
            self.__register["menu"].popup(None, None, None, 3, time)
        elif dialog == "program":
            self.__register["program"]()
        elif dialog == "about":
            self.__register["about"].show()
        else:
            if (self.__register[dialog].is_active() or force == "hide") and \
                force != "show":
                self.__register[dialog].hide()
                self.__current = None
            else:
                if self.__current: 
                    current_was_active = self.__current.is_active()

                    self.__current.hide()

                    if current_was_active and once:
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
            self.toggle("menu", once=True, time=e.time)
        elif e.button == 2 and "secondary" in self.__register: # Middle click
            self.toggle("secondary", once=True)
        elif e.button == 1 and "main" in self.__register:
            self.toggle("main", once=True)
        elif "program" in self.__register: # Act like launcher
            self.toggle("program", once=True)

    class AboutDialog(gtk.AboutDialog):
        """ Applet's About dialog """

        def __init__(self, parent):
            gtk.AboutDialog.__init__(self)

            self.__parent = parent

            self.set_name(self.__parent.meta["name"])

            if "version" in self.__parent.meta:
                self.set_version(self.__parent.meta["version"])
            if "description" in self.__parent.meta:
                self.set_comments(self.__parent.meta["description"])

            self.set_copyright("Copyright \xc2\xa9 " \
                + str(self.__parent.meta["copyright-year"]) \
                + " " + self.__parent.meta["author"])

            if "authors" in self.__parent.meta:
                self.set_authors(self.__parent.meta["authors"])
            if "artists" in self.__parent.meta:
                self.set_artists(self.__parent.meta["artists"])

            if "logo" in self.__parent.meta:
                self.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(self.__parent.meta["logo"], 48, 48))
                self.update_icon()
                parent.connect("height-changed", self.update_icon)

            # Connect some signals to be able to hide the window
            self.connect("response", self.response_event)
            self.connect("delete_event", self.delete_event)

        def delete_event(self, widget, event):
            return True

        def response_event(self, widget, response):
            if response < 0:
                self.hide()

        def update_icon(self, widget=None, event=None):
            """ Updates the applet's logo to be of the same height as the panel """

            height = self.__parent.get_height()
            self.set_icon(gtk.gdk.pixbuf_new_from_file_at_size(self.__parent.meta["logo"], height, height))

    class PreferencesDialog(gtk.Dialog):
        """ A Dialog window that has the title "<applet's name> Preferences",
        uses the applet's logo as its icon and has a Close button """

        def __init__(self, parent):
            gtk.Dialog.__init__(self, flags=gtk.DIALOG_NO_SEPARATOR)

            self.__parent = parent
            
            self.set_resizable(False)
            self.set_border_width(5)

            self.set_title(self.__parent.meta["name"] + " Preferences")
            self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

            if "logo" in self.__parent.meta:
                self.update_icon()
                parent.connect("height-changed", self.update_icon)

            self.connect("response", self.response_event)
            self.connect("delete_event", self.delete_event)

        def delete_event(self, widget, event):
            return True

        def response_event(self, widget, response):
            if response < 0:
                self.hide()

        def update_icon(self, widget=None, event=None):
            """ Updates the applet's logo to be of the same height as the panel """

            height = self.__parent.get_height()
            self.set_icon(gtk.gdk.pixbuf_new_from_file_at_size(self.__parent.meta["logo"], height, height))


class Title:
    def __init__(self, parent):
        """
        Creates a new Title object.

        @param parent: The parent applet of the title instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

    def show(self, w=None, e=None):
        """
        Show the applet title.
        """

        self.__parent.set_title_visibility(True)

    def hide(self, w=None, e=None):
        """
        Hides the applet title.
        """

        self.__parent.set_title_visibility(False)

    def set(self, text=""):
        """
        Sets the applet title.

        @param text: The new title text. Defaults to "".
        @type text: C{string}
        """

        self.__parent.set_title(text)


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

    def theme(self, name, set=None):
        """
        Get an icon from the default icon theme.

        @param name: The name of the theme icon.
        @type name: C{string}
        @param set: Whether to also set the icon. True by default.
        @type set: C{bool}
        """
        
        if set != None:
            print "WARNING: parameter 'set' is now deprecated because set_awn_icon() is used"

        self.__parent.set_awn_icon(self.__parent.meta["short"], name)

    def surface(self, surface, pixbuf=None, set=True):
        """
        Convert a C{cairo} surface to a C{gtk.gdk.Pixbuf}.

        @param surface: The C{cairo} surface to convert.
        @type surface: C{cairo.Surface}
        @param pixbuf: The reference to the pixbuf created from the surface.
        If you use this method multiple times, please keep a reference to
        this variable, or else your applet will leak memory.
        @type pixbuf: C{gtk.gdk.Pixbuf}
        @param set: Whether to also set the icon. True by default.
        @type set: C{bool}
        @return: The resultant pixbuf or None (if C{set} is C{True})
        @rtype: C{gtk.gdk.Pixbuf} or C{None}
        """

        if pixbuf is None:
            icon = extras.surface_to_pixbuf(surface)
        else:
            icon = extras.surface_to_pixbuf(surface, pixbuf)

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


class Modules: # DEPRECATED
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


class Errors:
    def __init__(self, parent):
        """
        Creates a new Modules object.

        @param parent: The parent applet of the icon instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

    def program(self, name, packagelist):
        """
        Tells the user that they need to install a program to use your applet.
        Note that this does not do any checking to determine whether the
        said program is installed. You must do all checking yourself - this is
        typically done with co-recursive functions.

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

        dlog = self.__parent.dialog.new("main", "<b>Error in %s:</b>" % \
            self.__parent.meta["name"])
        vbox = gtk.VBox()

        dlog.add(vbox)

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

    def module(self, name, packagelist, callback):
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

        dlog = self.__parent.dialog.new("main", "<b>Error in %s:</b>" % \
            self.__parent.meta["name"])
        vbox = gtk.VBox()

        dlog.add(vbox)

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
        vbox.add(text)

        # Submit button
        ok = gtk.Button(label = "OK, I've installed it")
        ok.show_all()
        vbox.add(ok)

        def qu(x):
            dlog.hide()
            self.get(name, packagelist, callback)

        ok.connect("clicked", qu)
        dlog.show_all()

    def general(self, error, callback):
        """
        Tells the user that they need to install a module to use your applet.
        This function will attempts to import the module, and if this is not
        possible, alert the user. Otherwise, it will call your callback with
        the module as the first (and only) argument

        @param error: the error itself.
        @type error: C{string} or C{Exception}
        @param callback: The function to be called when the user claims to have
            installed the necessary module. The module is passed as the first
            and only argument to the callback.
        @type callback: C{function}
        """

        # BaseException new to Python 2.5
        try:
            if isinstance(error, Exception) or \
                isinstance(error, BaseException):
                error = error.message
        except:
            # Python 2.4, so fallback without BaseException
            if type(error) == type(Exception()):
                error = error.message

        dlog = self.__parent.dialog.new("main", "<b>Error in %s:</b>" % \
            self.__parent.meta["name"])
        vbox = gtk.VBox()

        dlog.add(vbox)

        text = gtk.Label("There seem to be problems in the %s applet. \n\nHere is the error given:\n\n<i>%s</i>" % (self.__parent.meta["name"], error))
        text.set_line_wrap(True)
        text.set_use_markup(True)
        text.set_justify(gtk.JUSTIFY_FILL)
        vbox.add(text)

        # Submit button
        ok = gtk.Button(label = "Close")
        vbox.add(ok)

        def qu(x):
            dlog.hide()
            callback()

        ok.connect("clicked", qu)

        dlog.show_all() # We want the dialog to show itself right away


class Networking:
    def __init__(self, parent):
        """
        Creates a new Settings object. Note that the Settings object should be
        used as a dictionary.

        @param parent: The parent applet of the settings instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

    def __get_thread(self, url, callback):
        callback(urllib.urlopen(url))

    def get(self, url, callback):
        """
        Get the contents of the page located on the internet.

        @param url: The URL of the page to get
        @type url: C{string}
        @param callback: The function to call after the page is retrieved. The file-like object will be passed as the first argument
        @type callback: C{function}
        """

        gobject.idle_add(self.__get_thread(url, callback))


class Settings:
    def __init__(self, parent):
        """
        Creates a new Settings object. Note that the Settings object should be
        used as a dictionary.

        @param parent: The parent applet of the settings instance.
        @type parent: L{Applet}
        """

        self.__parent = parent

        try:
            folder = self.__parent.meta["short"]
        except:
            folder = ""

        self.client = self.AWNConfigUser(folder)

    def load(self, dict, push_defaults=True):
        """
        Synchronize the values from the given dictionary with the stored
        settings, replacing values in the given dictionary if they have been
        overridden.

        @param dict: Default values for the dictionary.
        @type parent: L{dict}
        @param push_defaults: Whether to store non-overridden defaults in
        the settings backend. True by default.
        @type parent: L{bool}
        """

        for key in dict:
            if key in self:
                dict[key] = self[key]
            elif push_defaults:
                self[key] = dict[key]

    def cd(self, folder=None):
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

    def __contains__(self, item):
        """
        Test if a key exists in the current directory.

        @param item: A key name
        @type key: C{string}
        """

        try:
            self[item]
        except:
            return False
        else:
            return True

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

        self.__parent.errors.module("gnomekeyring", { \
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

    def register(self, callback, sec):
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

    time = register # DEPRECATED

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

        print "WARNING: notify.require() is no longer necessary"
        pass

    def send(self, subject=None, body="", icon="", attention=True):
        """
        Sends a new libnotify message.

        @param subject: The subject of your message. If blank, "Message from
            [applet - full name]" is used.
        @type subject: C{string}
        @param body: The main body of your message. Blank by default.
        @type body: C{string}
        @param icon: The full absolute path to the name of the icon to use.
        @type icon: C{string}
        @param attention: Whether or not to call the attention effect after
            sending the message. True by default.
        @type attention: C{bool}
        """

        if not subject:
            subject = '"' + "Message From " + self.__parent.meta["name"] + '"'

        return extras.notify_message(subject, body, icon, 0, False)


class Effects:
    def __init__(self, parent):
        """
        Creates a new Effects object.

        @param parent: The parent applet of the effects instance.
        @type parent: L{Applet}
        """

        self.__parent = parent
        self.__effects = self.__parent.get_effects()

    def attention(self):
        """
        Launches the notify effect. Should be used when the user's attention
        is required.
        """

        awn.awn_effect_start_ex(self.__effects, "attention", 0, 0, 1)

    notify = attention # DEPRECATED

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
        Updates the meta instance with new information.

        @param info: Default values for the meta dictionary
        @type info: C{dict}
        """

        self.__info.update(info)

    def __getitem__(self, key):
        """
        Get a key from the dictionary.

        @param key: The key
        @type key: C{string}
        """

        return self.__info[key]

    def __setitem__(self, key, value):
        """
        Set a key in the dictionary.

        @param key: The key
        @type key: C{string}
        @param value: The value
        @type value: C{string}
        """
        self.__info[key] = value

    def __delitem__(self, key):
        """
        Delete a key from the dictionary.

        @param key: The key
        @type key: C{string}
        """

        del self.__info[key]

    def keys(self):
        """
        Returns a list of keys from the dictionary.
        """

        return self.__info.keys()

    def __contains__(self, key):
        """
        Returns True if the dictionary contains the key, False otherwise.

        @param key: The key
        @type key: C{string}
        """
        
        return key in self.__info


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
        self.title = Title(self)
        self.module = Modules(self)
        self.errors = Errors(self)
        self.settings = Settings(self)
        self.dialog = Dialogs(self) # Dialogs depends on settings
        self.timing = Timing(self)
        self.keyring = KeyRing(self)
        self.notify = Notify(self)
        self.effects = Effects(self)
        self.network = Networking(self)

        # Connect the necessary events to the sub-objects.
        self.connect("button-press-event", self.dialog.click)


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
    gobject.threads_init() # Threading for Networking
    gtk.main() # Start
