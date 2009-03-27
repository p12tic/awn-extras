# AWN Applet Library - simplified APIs for programming applets for AWN.
#
# Copyright (C) 2007 - 2008  Pavel Panchekha <pavpanchekha@gmail.com>
#               2008 - 2009  onox <denkpadje@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import sys

import gobject
import pygtk
pygtk.require("2.0")
import gtk

import awn
import awn.extras as extras
import cairo
import cPickle as cpickle  # For object serialization into gconf
import types  # For type checking for gconf/settings
import urllib

___file___ = sys.argv[0]
# Basically, __file__ = current file location
# sys.argv[0] = file name or called file
# Since awnlib is in site-packages, __file__ refers to something there
# For relative paths to work, we need a way of determining where the
# User applet is. So this bit of magic works.

_globalRegister = {}

bug_report_link = "https://launchpad.net/awn-extras/+filebug"


def create_frame(parent, label):
    vbox = gtk.VBox(spacing=6)
    parent.add(vbox)

    label = gtk.Label("<b>" + label + "</b>")
    label.set_use_markup(True)
    label.props.xalign = 0.0
    vbox.add(label)

    alignment = gtk.Alignment()
    alignment.set_padding(0, 0, 12, 0)
    vbox.add(alignment)

    frame_vbox = gtk.VBox(spacing=6)
    alignment.add(frame_vbox)

    return frame_vbox


def deprecated(old, new):
    def decorator(f):
        def wrapper(*args, **kwargs):
            m = "\nawnlib warning in %s:\n\t%s is deprecated; use %s instead\n"
            print m % (os.path.split(___file___)[1], old, new)
            return f(*args, **kwargs)
        return wrapper
    return decorator


class KeyRingError:

    def __init__(self, str):
        self.msg = str

    def __str__(self):
        return self.msg


class Dialogs:

    __special_dialogs = ("menu", "program", "about", "preferences")

    def __init__(self, parent):
        """Create an instance of Dialogs. Creates a context menu,
        and an About dialog, which is added to the menu.

        @param parent: The parent applet of the dialogs instance.
        @type parent: L{Applet}

        """
        self.__parent = parent

        self.__register = {}
        self.__current = None

        self.menu = self.new("menu")

        meta_keys = self.__parent.meta.keys()

        # Create the About dialog if the applet provides the necessary metadata
        if all([key in meta_keys for key in ("name", "author",
                                             "copyright-year")]):
            about_dialog = self.new("about")

            about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
            self.menu.append(about_item)
            about_item.connect("activate", lambda w: self.toggle("about"))

        self.__parent.settings.cd("shared")

        if "dialog_focus_loss_behavior" in self.__parent.settings:
            self.__loseFocus = self.__parent.settings[
                "dialog_focus_loss_behavior"]
        else:
            self.__loseFocus = True

        self.__parent.settings.cd()

        parent.connect("button-press-event", self.button_press_event_cb)

    def new(self, dialog, title=None, focus=True):
        """Create a new AWN dialog.

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
        elif dialog == "program":
            dlog = lambda: None
        elif dialog == "about":
            dlog = self.AboutDialog(self.__parent)
        elif dialog == "preferences":
            dlog = self.PreferencesDialog(self.__parent)

            position = len(self.menu)
            if "about" in self.__register:
                position = position - 1

            prefs_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
            self.menu.insert(prefs_item, position)
            prefs_item.connect("activate", lambda w: self.toggle(
               "preferences", "show"))
        else:
            dlog = awn.Dialog(self.__parent)

        self.register(dialog, dlog, focus)

        if dialog not in self.__special_dialogs and title:
            dlog.set_title(" " + title + " ")

        return dlog

    def register(self, dialog, dlog, focus=True):
        """Register a dialog.

        @param dialog: The name to use for the dialog. The predefined values
                       are main, secondary, menu, and program.
        @type dialog: C{string}
        @param dlog: The actual dialog or menu or function.
        @type dlog: C{function}, C{gtk.Menu}, or C{awn.AppletDialog}
        @param focus: Whether to bind focus in-out handlers for the dialog.
        @type focus: C{bool}

        """
        if focus and dialog not in self.__special_dialogs and self.__loseFocus:
            def dialog_focus_out_cb(widget, event):
                try:
                    parent = dlog.get_focus().get_parent()
                    combobox_shown = parent.get_property("popup-shown")
                except:
                    combobox_shown = False
                if not combobox_shown:
                    self.__current = None
                    dlog.hide()
            dlog.connect("focus-out-event", dialog_focus_out_cb)

        self.__register[dialog] = dlog

    def toggle(self, dialog, force="", once=False, time=0):
        """Show or hide a dialog.

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
        assert dialog in self.__register, "Dialog must be registered"

        if dialog == "menu":
            self.__register["menu"].show_all()
            self.__register["menu"].popup(None, None, None, 3, time)
        elif dialog == "program":
            self.__register["program"]()
        elif dialog == "about":
            self.__register["about"].show()
        else:
            if force == "hide" or (self.__register[dialog].is_active() and \
                                       force != "show"):
                self.__register[dialog].hide()
                self.__current = None

                # Because the dialog is now hidden, show the title again
                self.__parent.tooltip.show()
            else:
                if self.__current is not None and self.__current not in \
                        self.__special_dialogs:
                    current = self.__register[self.__current]

                    current_was_active = current.is_active()

                    current.hide()

                    if current_was_active and once:
                        self.__current = None
                        return

                self.__register[dialog].show_all()
                self.__current = dialog

    def hide(self):
        """Hide the currently visible dialog.

        """
        if self.__current is not None:
            self.__register[self.__current].hide()
            self.__current = None

    def button_press_event_cb(self, widget, event):
        """Responds to click events. Only called by GTK+.

        """
        if event.button == 3 and "menu" in self.__register:  # Right
            self.toggle("menu", once=True, time=event.time)
        elif event.button == 2 and "secondary" in self.__register:  # Middle
            self.toggle("secondary", once=True)
        elif event.button == 1 and "main" in self.__register:
            self.toggle("main")
        elif "program" in self.__register:  # Act like launcher
            self.toggle("program", once=True)

    class AboutDialog(gtk.AboutDialog):

        """Applet's About dialog.

        """

        def __init__(self, parent):
            gtk.AboutDialog.__init__(self)

            self.__parent = parent

            self.set_name(parent.meta["name"])

            if "version" in parent.meta:
                self.set_version(parent.meta["version"])
            if "description" in parent.meta:
                self.set_comments(parent.meta["description"])

            copyright_info = (parent.meta["copyright-year"], \
                                  parent.meta["author"])
            self.set_copyright("Copyright \xc2\xa9 %s %s" % copyright_info)

            if "authors" in parent.meta:
                self.set_authors(parent.meta["authors"])
            if "artists" in parent.meta:
                self.set_artists(parent.meta["artists"])

            if "logo" in parent.meta:
                self.set_logo(gtk.gdk.pixbuf_new_from_file_at_size( \
                        parent.meta["logo"], 48, 48))

                self.update_logo_icon()
                parent.connect_size_changed(self.update_logo_icon)
            elif "theme" in parent.meta:
                # It is assumed that the C{awn.Icons}
                # object has been set via set_awn_icon() in C{Icon}
                self.set_logo(parent.get_icon().get_icon_at_size(48))

                self.update_theme_icon()
                parent.connect_size_changed(self.update_theme_icon)

            # Connect some signals to be able to hide the window
            self.connect("response", self.response_event)
            self.connect("delete_event", self.delete_event)

        def delete_event(self, widget, event):
            return True

        def response_event(self, widget, response):
            if response < 0:
                self.hide()

        def update_logo_icon(self):
            """Set the applet's logo to be of the same height as the panel.

            """
            size = self.__parent.get_size()
            self.set_icon(gtk.gdk.pixbuf_new_from_file_at_size( \
                    self.__parent.meta["logo"], size, size))

        def update_theme_icon(self):
            """Set the applet's logo to be of the same height as the panel.

            """
            self.set_icon(self.__parent.get_icon() \
                .get_icon_at_size(self.__parent.get_size()))

    class PreferencesDialog(gtk.Dialog):

        """A Dialog window that has the title "<applet's name> Preferences",
        uses the applet's logo as its icon and has a Close button.

        """

        def __init__(self, parent):
            gtk.Dialog.__init__(self, flags=gtk.DIALOG_NO_SEPARATOR)

            self.__parent = parent

            self.set_resizable(False)
            self.set_border_width(5)

            self.set_title(parent.meta["name"] + " Preferences")
            self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

            if "logo" in parent.meta:
                self.update_logo_icon()
                parent.connect_size_changed(self.update_logo_icon)
            elif "theme" in parent.meta:
                self.update_theme_icon()
                parent.connect_size_changed(self.update_theme_icon)

            self.connect("response", self.response_event)
            self.connect("delete_event", self.delete_event)

        def delete_event(self, widget, event):
            return True

        def response_event(self, widget, response):
            if response < 0:
                self.hide()

        def update_logo_icon(self):
            """Update the logo to be of the same height as the panel.

            """
            size = self.__parent.get_size()
            self.set_icon(gtk.gdk.pixbuf_new_from_file_at_size( \
                self.__parent.meta["logo"], size, size))

        def update_theme_icon(self):
            """Updates the logo to be of the same height as the panel.

            """
            self.set_icon(self.__parent.get_icon() \
                .get_icon_at_size(self.__parent.get_size()))


class Title:

    def __init__(self, parent):
        """Create a new Title object.

        @param parent: The parent applet of the title instance.
        @type parent: L{Applet}

        """
        self.__parent = parent

        self.__tooltip = parent.get_icon().get_tooltip()
        self.set(parent.meta["name"])

    def disable_toggle_on_click(self):
        self.__tooltip.props.toggle_on_click = False

    def is_visible(self):
        return (self.__tooltip.flags() & gtk.VISIBLE) != 0

    def show(self):
        """Show the applet title.

        """
        self.__tooltip.show_all()

    def hide(self):
        """Hide the applet title.

        """
        self.__tooltip.hide_all()

    def set(self, text):
        """Set the applet title.

        @param text: The new title text. Defaults to "".
        @type text: C{string}

        """
        self.__parent.set_tooltip_text(text)

    def connect_becomes_visible(self, callback):
        assert callable(callback)
        self.__tooltip.connect("map-event", lambda w, e: callback())


class Icon:

    APPLET_SIZE = "applet-size"

    def __init__(self, parent):
        """Create a new Icon object.

        @param parent: The parent applet of the icon instance.
        @type parent: L{Applet}

        """
        self.__parent = parent

        self.__previous_context = None

        # Set the themed icon to set the C{awn.Icons} object
        if "theme" in parent.meta:
            # TODO does not handle multiple icons yet
            self.theme(parent.meta["theme"])

    def file(self, file, set=True, size=None):
        """Get an icon from a file location.

        @param file: The path to the file. Can be relative or absolute.
        @type file: C{string}
        @param set: Whether to also set the icon. True by default.
        @type set: C{bool}
        @param size: Width and height of icon.
        @type size: C{int}
        @return: The resultant pixbuf or None (if C{set} is C{True})
        @rtype: C{gtk.gdk.Pixbuf} or C{None}

        """
        if file[0] != "/":
            file = os.path.join(os.path.abspath( \
                os.path.dirname(___file___)), file)

        if size is None:
            icon = gtk.gdk.pixbuf_new_from_file(file)
        else:
            if size is self.__class__.APPLET_SIZE:
                size = self.__parent.get_size()
            icon = gtk.gdk.pixbuf_new_from_file_at_size(file, size, size)

        if set:
            self.set(icon)
        else:
            return icon

    def theme(self, name):
        """Set an icon from the default icon theme. The resultant
        pixbuf will be returned.

        @param name: The name of the theme icon.
        @type name: C{string}
        @return: The resultant pixbuf
        @rtype: C{gtk.gdk.Pixbuf}

        """
        return self.__parent.set_icon_name(self.__parent.meta["short"], name)

    def surface(self, surface, pixbuf=None, set=True):
        """Convert a C{cairo} surface to a C{gtk.gdk.Pixbuf}.

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
        if set:
            self.set_icon_surface(surface)
        else:
            if pixbuf is None:
                return extras.surface_to_pixbuf(surface)
            else:
                return extras.surface_to_pixbuf(surface, pixbuf)

    def set(self, icon):
        """Set a C{gtk.gdk.pixbuf} or C{cairo.Context} as your applet icon.

        @param icon: The icon to set your applet icon to.
        @type icon: C{gtk.gdk.Pixbuf} or C{cairo.Context}

        """
        if isinstance(icon, cairo.Context):
            self.__parent.set_icon_context(icon)

            if self.__previous_context != icon:
                del self.__previous_context
                self.__previous_context = icon
        else:
            self.__parent.set_icon_pixbuf(icon)

    def hide(self):
        """Hide the applet's icon.

        """
        self.__parent.hide()


class Errors:

    def __init__(self, parent):
        """Create a new Modules object.

        @param parent: The parent applet of the icon instance.
        @type parent: L{Applet}

        """
        self.__parent = parent

    def module(self, scope, name):
        """Tell the user that they need to install a module to use your applet.
        This function will attempts to import the module, and if this is not
        possible, alert the user. Otherwise, it will call your callback with
        the module as the first (and only) argument

        @param scope: The dictionary that contains the globals to
                      import the module into
        @type scope: C{dict}
        @param name: the name of the module that must be installed.
        @type name: C{string}

        """
        try:
            """ Don't add the module to globals[name], otherwise
            awn.check_dependencies() won't show an error dialog. """
            scope[name] = __import__(name, scope)
        except ImportError:
            self.__parent.icon.theme("dialog-error")
            self.__parent.tooltip.set("Python module %s not found" % name)

            awn.check_dependencies(scope, name)

    def general(self, error, callback=None, traceback=None):
        """Tell the user that an error has occured.

        @param error: the error itself.
        @type error: C{string} or C{Exception}
        @param callback: The function called when the user closes the dialog
        @type callback: C{function}
        @param traceback: Formatted traceback, can be copied to clipboard
        via button in dialog.
        @type traceback: C{str}

        """
        assert isinstance(error, Exception) or type(error) is str

        if traceback is not None:
            traceback = "".join(traceback)[:-1]

        args = {"message": "", "url": None}
        if isinstance(error, Exception):
            error_type = type(error).__name__
            error = error.message
            if traceback is not None:
                print "\n".join(["-"*80, traceback, "-"*80])
                args["message"] = "Visit Launchpad and paste the traceback" \
                                    + " when reporting the bug."
                args["url"] = bug_report_link
        else:
            error_type = "Error"

        dialog = self.ErrorDialog(self.__parent, error_type, error, **args)

        if traceback is not None:
            copy_button = gtk.Button("Copy traceback to clipboard")
            copy_button.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
            dialog.hbox.pack_start(copy_button, expand=False)
            def clicked_cb(widget):
                clipboard = gtk.clipboard_get()
                clipboard.set_text(traceback)
                clipboard.store()
            copy_button.connect("clicked", clicked_cb)

        if callable(callback):
            def response_cb(widget, response):
                if response < 0:
                    callback()
            dialog.connect("response", response_cb)

        dialog.show_all()

    class ErrorDialog(gtk.MessageDialog):

        """A MessageDialog window that shows an error.

        """

        def __init__(self, parent, error_type, title, message="", url=None):
            gtk.MessageDialog.__init__(self, type=gtk.MESSAGE_ERROR, message_format=title)

            self.__parent = parent

            self.set_resizable(False)
            self.set_border_width(5)

            self.set_title("%s in %s" % (error_type, parent.meta["name"]))

            self.hbox = gtk.HBox(spacing=6)
            self.action_area.add(self.hbox)

            close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
            close_button.connect("clicked", lambda w: self.emit("response", gtk.RESPONSE_CLOSE))
            self.hbox.add(close_button)

            if len(message) > 0:
                self.format_secondary_markup(message)

            if url is not None:
                alignment = gtk.Alignment(xalign=0.5, xscale=0.0)
                alignment.add(gtk.LinkButton(url))
                self.vbox.pack_start(alignment, expand=False)

            if "logo" in parent.meta:
                self.update_logo_icon()
                parent.connect_size_changed(self.update_logo_icon)
            elif "theme" in parent.meta:
                self.update_theme_icon()
                parent.connect_size_changed(self.update_theme_icon)

            self.connect("response", self.response_event)
            self.hide_on_delete()

        def response_event(self, widget, response):
            if response < 0:
                self.hide()

        def update_logo_icon(self):
            """Update the logo to be of the same height as the panel.

            """
            size = self.__parent.get_size()
            self.set_icon(gtk.gdk.pixbuf_new_from_file_at_size( \
                self.__parent.meta["logo"], size, size))

        def update_theme_icon(self):
            """Updates the logo to be of the same height as the panel.

            """
            self.set_icon(self.__parent.get_icon() \
                .get_icon_at_size(self.__parent.get_size()))


class Settings:

    def __init__(self, parent):
        """Create a new Settings object. Note that the Settings object
        should be used as a dictionary. The default folder: the short
        name, and if the applet has requested the settings-per-instance
        option, a '-', and the uid, if the meta dictionary contains the
        "short" key. Otherwise the default folder will be just the uid
        of the applet.

        @param parent: The parent applet of the settings instance.
        @type parent: L{Applet}

        """
        self.__dict = None
        self.__callables = {}

        if "short" in parent.meta:
            if parent.meta.has_option("settings-per-instance"):
                self.__folder = "%s-%s" % (parent.meta["short"], parent.uid)
            else:
                self.__folder = parent.meta["short"]
        else:
            self.__folder = parent.uid

        self.__client = self.ConfigClient(self.__folder)

    def load(self, dict, push_defaults=True):
        """Synchronize the values from the given dictionary with the stored
        settings, replacing values in the given dictionary if they have been
        overridden.

        @param dict: Default values for the dictionary.
        @type parent: L{dict}
        @param push_defaults: Whether to store non-overridden defaults in
        the settings backend. True by default.
        @type parent: L{bool}

        """
        if self.__dict is not None:
            raise RuntimeError("settings already loaded")

        self.__dict = dict

        for key in dict:
            if key in self:
                dict[key] = self[key]
            elif push_defaults:
                self[key] = dict[key]

    def load_preferences(self, dict_tuples, push_defaults=True):
        """Synchronize the values from the tuples in the given dictionary
        with the stored settings, use the callable to be called when the value
        is changed, and initialize and connect the provided Gtk+ widget. 

        Returns a "read-only" dictionary containing, now and in the future,
        up-to-date values.

        A callable, optionally provided at the second index in the tuple,
        will be called when the value of the setting is changed.
        If the tuple provides a certain Gtk+ widget at the third index,
        then this widget will be initialized with the value of the setting,
        and changes in the value of the widget will be reflect in the returned
        dictionary and settings backend.

        @param dict: Default values for the dictionary.
        @type parent: L{dict}
        @param push_defaults: Whether to store non-overridden defaults in
        the settings backend. True by default.
        @type parent: L{bool}

        """
        if self.__dict is not None:
            raise RuntimeError("settings already loaded")

        self.__dict = {}

        for key, values in dict_tuples.iteritems():
            is_tuple = type(values) is tuple
            default_value = values[0] if is_tuple else values

            if key in self:
                self.__dict[key] = self[key]
            else:
                self.__dict[key] = default_value
                if push_defaults:
                    self[key] = default_value

            if not is_tuple or len(values) == 1:
                continue

            self.__callables[key] = values[1]

            if len(values) == 2:
                continue

            key_widget = values[2]
            widget_type = type(key_widget)

            if isinstance(key_widget, gtk.ToggleButton):
                def toggled_cb(widget, name):
                    self[name] = widget.get_active()
                key_widget.set_active(self.__dict[key])
                key_widget.connect("toggled", toggled_cb, key)
            elif widget_type is gtk.SpinButton:
                def value_changed_cb(widget, name):
                    self[name] = widget.get_value_as_int()
                key_widget.set_value(self.__dict[key])
                key_widget.connect("value-changed", value_changed_cb, key)
            else:
                raise RuntimeError("%s is unsupported" % widget_type.__name__)

        return self.__dict

    def cd(self, folder=None, raw=False):
        """Change to another folder. Note that this will change folders to e.g.
        /apps/avant-window-navigator/applets/[folder] in the GConf
        implementation and to just /applets/[folder] in the iniKey
        implementation. If the C{raw} parameter if False, "/applets" is
        prepended to C{folder}.

        @param folder: The folder to use for your applet. If not given, the
            default folder is used.
        @type folder: C{string}
        @param raw: If False, "/applets" is prepended to C{folder}.
        @type raw: C{bool}

        """
        if not folder:
            folder = self.__folder

        if not raw:
            folder = os.path.join("applets", folder)

        self.__client.cd(folder)

    def notify(self, key, callback):
        """Set up a function to be executed every time a key changes. Note that
        this works best (if at all) on whole folders, not individual keys.

        @param key: The key or folder to monitor for changes.
        @type key: C{string}
        @param callback: The function to call upon changes.
        @type callback: C{function}

        """
        self.__client.notify(key, callback)

    def __set(self, key, value, value_type="string"):
        if key in self:
            try:
                self.__client.set(key, value)
            except AttributeError:
                self.__client.new(key, value, value_type)
        else:
            self.__client.new(key, value, value_type)

    def __get(self, key):
        value = self.__client.get(key)
        if type(value) is str and value[:9] == "!pickle;\n":
            value = cpickle.loads(value[9:])
        return value

    def __getitem__(self, key):
        """Get a key from the currect directory.

        @param key: A relative path to the correct key
        @type key: C{string}
        @return: The value of the key
        @rtype: C{object}

        """
        return self.__get(key)

    __setting_types = {
        types.BooleanType: "bool",
        types.IntType: "int",
        types.LongType: "int",
        types.FloatType: "float",
        types.StringType: "string"
    }

    def __setitem__(self, key, value):
        """Set or create a key from the currect directory.

        @param key: A relative path to the correct key
        @type key: C{string}

        """
        unpickled_value = value

        if type(value) in self.__setting_types.keys():
            value_type = self.__setting_types[type(value)]
        else:
            value = "!pickle;\n%s" % cpickle.dumps(value)
            value_type = "string"
        self.__set(key, value, value_type)

        # Update the value in the loaded dictionary
        if self.__dict is not None:
            self.__dict[key] = unpickled_value

            if key in self.__callables:
                self.__callables[key](unpickled_value)

    def __delitem__(self, key):
        """Delete a key from the currect directory.

        @param key: A relative path to the correct key
        @type key: C{string}

        """
        self.__client.delete(key)

    def __contains__(self, key):
        """Test if a key exists in the current directory.

        @param key: A relative path to the correct key
        @type key: C{string}

        """
        return self.__client.contains(key)

    class ConfigClient:

        def __init__(self, folder):
            """Create a new config client.

            @param folder: Folder to start with.
            @type folder: C{string}

            """
            self.__client = awn.Config()

            self.cd(folder)

        def cd(self, folder):
            """Change the current directory.

            @param folder: The folder to change into.
            @type folder: C{string}
 
            """
            self.__folder = folder

        def notify(self, key, callback):
            """Set up a function to be executed every time a key changes. Works
            best (if at all) on whole folders, not individual keys.

            @param key: The key or folder to monitor for changes.
            @type key: C{string}
            @param callback: The function to call upon changes.
            @type callback: C{function}

            """
            self.__client.notify_add(self.__folder, key, callback)

        def set(self, key, value):
            """Set an existing key's value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @param value: The value to set the key to.
            @type value: C{bool}, C{int}, C{float}, or C{string}

            """
            try:
                f = getattr(self.__client, "set_%s" % self.type(key))
            except:
                raise ValueError("Could not set new value of '%s'" % key)
            f(self.__folder, key, value)

        def new(self, key, value, value_type):
            """Create a new key and set its value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @param value: The value to set the key to.
            @type value: C{bool}, C{int}, C{float}, or C{string}
            @param type: The type to make the new key.
            @type type: C{string}; "bool", "int", "float", or "string"

            """
            f = getattr(self.__client, "set_%s" % value_type)
            f(self.__folder, key, value)

        def get(self, key):
            """Get an existing key's value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @return: The value of the key
            @rtype: C{object}

            """
            try:
                f = getattr(self.__client, "get_%s" % self.type(key))
            except:
                raise ValueError("'%s' does not exist" % key)
            return f(self.__folder, key)

        def contains(self, key):
            """Test if the key maps to a value.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @return: True if the key maps to a value, False otherwise
            @rtype: C{bool}

            """
            return self.__client.exists(self.__folder, key)

        def delete(self, key):
            """Delete an existing key. Not yet implemented; will raise the
            NotImplementedError. Will work when implemented upstream.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}

            """
            raise NotImplementedError("AWNConfig does not support deleting")

        def type(self, key):
            """Get an existing key's type.

            @param key: The name of the key, relative to the current folder.
            @type key: C{string}
            @return: The type of the key
            @rtype: C{object}

            """
            return self.__client.get_value_type(self.__folder, key).value_nick


class Keyring:

    def __init__(self, parent):
        """Create a new Keyring object. This includes importing the keyring
        module and connecting to the daemon.

        @param parent: The parent applet of the keyring instance.
        @type parent: L{Applet}

        """
        self.__parent = parent

        self.__parent.errors.module(globals(), "gnomekeyring")

        if not gnomekeyring.is_available():
            raise KeyRingError("Keyring not available")

        keyring_list = gnomekeyring.list_keyring_names_sync()

        if len(keyring_list) == 0:
            raise KeyRingError("No keyrings available")

        try:
            gnomekeyring.get_default_keyring_sync()
        except gnomekeyring.NoKeyringDaemonError:
            raise KeyRingError("Had trouble connecting to daemon")

    def new(self, name=None, pwd=None, attrs={}, type="generic"):
        """Create a new keyring key.

        @param name: The display name of the key. If omitted, an empty key is
            returned.
        @type name: C{string}
        @param pwd: The password stored in the key. If omitted, empty key is
            returned.
        @type pwd: C{string}
        @param attrs: Other attributes stored in the key. By default: {}
        @type attrs: C{dict}
        @param type: The type of key. By default: "generic"
        @type type: C{string}; "generic", "network", or "note"
        @return: A new L{Key} object
        @rtype: L{Key}

        """
        k = self.Key()
        if name and pwd:
            k.set(name, pwd, attrs, type)
        return k

    def from_token(self, token):
        """Load the key with the given token.

        @param token: The password token of the key
        @type token: C{int} or C{long}
        @return: A new L{Key} object
        @rtype: L{Key}

        """
        k = self.Key()
        k.token = token
        return k

    class Key(object):

        def __init__(self, token=0):
            """Create a new key.

            @param keyring: The keyring module.
            @type keyring: C{module}
            @param token: The token of an already-existing key. Optional.
            @type token: C{long}

            """
            self.token = token

        def set(self, name, pwd, attrs={}, type="generic"):
            """Create a new keyring key. Note that if another key
            exists with the same name, it will be overwritten.

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
                type = gnomekeyring.ITEM_NETWORK_PASSWORD
            elif type == "note":
                type = gnomekeyring.ITEM_NOTE
            else:  # Generic included
                type = gnomekeyring.ITEM_GENERIC_SECRET

            self.token = gnomekeyring.item_create_sync(None, type, name, \
                attrs, pwd, True)

        def delete(self):
            """Delete the current key. Will also reset the token. Note that
            "del [Key]" will not delete the key itself; that would be too
            destructive. delete() MUST be called manually.

            """
            gnomekeyring.item_delete_sync(None, self.token)
            self.token = 0

        def __get(self):
            return gnomekeyring.item_get_info_sync(None, self.token)

        def __getAttrs(self):
            return gnomekeyring.item_get_attributes_sync(None, self.token)

        def __setAttrs(self, a):
            return gnomekeyring.item_set_attributes_sync(None, self.token, a)

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

    """Provides utilities to register a function to be called periodically
    or once after a specified delay.

    """

    def __init__(self, parent):
        """Create a new Timing object.

        @param parent: The parent applet of the timing instance.
        @type parent: L{Applet}

        """
        self.__parent = parent

    def register(self, callback, seconds, start=True):
        """Register a function to be called periodically.

        @param callback: Function to be called.
        @type callback: C{function}
        @param seconds: Number of seconds within each call.
        @type seconds: C{float} or C{int}
        @param start: Whether to start the callback automatically
        @type start: C{bool}
        @return: A L{Callback} object for the C{callback} parameter
        @rtype: L{Callback}

        """
        def callback_wrapper():
            callback()
            return True
        cb = self.Callback(callback_wrapper, seconds)
        if start:
            cb.start()
        return cb

    def delay(self, callback, seconds, start=True):
        """Delay the execution of the given callback.

        @param callback: Function
        @type callback: C{function}
        @param seconds: Number of seconds to delay function call
        @type seconds: C{float} or C{int}
        @return: A L{Callback} object for the C{callback} parameter
        @rtype: L{Callback}

        """
        def callback_wrapper():
            callback()
            return False
        cb = self.Callback(callback_wrapper, seconds)
        if start:
            cb.start()
        return cb

    class Callback:

        """Wrapper around a callback function to provide ways to start and
        stop the function, to change the interval or to test if the callback
        is scheduled to run.

        """

        def __init__(self, callback, seconds):
            """Create a new C{Callback} object.

            @param callback: The function to wrap the Callback around.
            @type callback: C{function}
            @param seconds: Number of seconds within each call.
            @type seconds: C{float} or C{int}

            """
            assert seconds > 0.0

            self.__callback = callback
            self.__seconds = seconds
            self.__timer_id = None

        def is_started(self):
            """Return True if the callback has been scheduled to run after
            each interval, False if the callback is stopped.

            @return: True if the callback is running, False otherwise
            @rtype: L{bool}

            """
            return self.__timer_id is not None

        def start(self):
            """Start executing the callback periodically.

            @return: True if the callback was started, False otherwise
            @rtype: L{bool}

            """
            if self.__timer_id is None:
                if int(self.__seconds) == self.__seconds:
                    self.__timer_id = gobject.timeout_add_seconds( \
                        int(self.__seconds), self.__callback)
                else:
                    self.__timer_id = gobject.timeout_add( \
                        int(self.__seconds * 1000), self.__callback)
                return True
            return False

        def stop(self):
            """Stop the callback from running again if it was scheduled
            to run.

            @return: True if the callback was stopped, False otherwise
            @rtype: L{bool}

            """
            if self.__timer_id is not None:
                gobject.source_remove(self.__timer_id)
                self.__timer_id = None
                return True
            return False

        def change_interval(self, seconds):
            """Change the interval and restart the callback if it was scheduled
            to run.

            @param seconds: Number of seconds within each call.
            @type seconds: C{float} or C{int}

            """
            assert seconds > 0.0

            self.__seconds = seconds

            # Restart if the callback was scheduled to run
            if self.stop():
                self.start()


class Notify:

    def __init__(self, parent):
        """Create a new Notify object.

        @param parent: The parent applet of the notify instance.
        @type parent: L{Applet}

        """
        self.__parent = parent

    def send(self, subject=None, body="", icon="", timeout=0, attention=True):
        """Show a new notification via libnotify.

        @param subject: The subject of your message. If blank, "Message from
            [applet - full name]" is used.
        @type subject: C{string}
        @param body: The main body of your message. Blank by default.
        @type body: C{string}
        @param icon: The full absolute path to the name of the icon to use.
        @type icon: C{string}
        @param timeout: Timeout in seconds after which the message closes
        @type timeout: C{int}
        @param attention: Whether or not to call the attention effect after
            sending the message. True by default.
        @type attention: C{bool}

        """
        if not subject:
            subject = '"' + "Message From " + self.__parent.meta["name"] + '"'

        timeout *= 1000
        return extras.notify_message(subject, body, icon, timeout, False)


class Effects:

    def __init__(self, parent):
        """Create a new Effects object.

        @param parent: The parent applet of the effects instance.
        @type parent: L{Applet}

        """
        self.__effects = parent.get_icon().get_effects()

    def attention(self):
        """Launch the notify effect.

        Should be used when the user's attention is required.

        """
        self.__effects.start("attention")

    def launch(self):
        """Launch the launch effect.

        Should be used when launching another program.

        """
        self.__effects.start("launching")


class Meta:

    def __init__(self, parent, info={}, options=()):
        """Create a new Meta object.

        @param parent: The parent applet of the meta instance.
        @type parent: L{Applet}
        @param info: Values for the meta dictionary
        @type info: C{dict}
        @param options: Options to set. Format:
            (option", "option", ("option": True|False), ("option":
                ("suboption", "suboption", ("suboption": True|False), ...)))

        """
        assert "name" in info

        self.__parent = parent

        self.__info = info

        self.__options = {}
        self.options(options)

    def update(self, info):
        """Update the meta instance with new information.

        @param info: Updated values for the meta dictionary
        @type info: C{dict}

        """
        self.__info.update(info)

    def options(self, opts):
        """Update the options the applet has set

        @param opts: Options to set
        @type opts: C{list} or C{tuple}

        """
        self.__options.update(self.__parse_options(opts))

    def has_option(self, option):
        """Check if the applet has set a specific option.

        @param option: Option to check. Format: "option/suboption/suboption"
        @type option: C{str}

        """
        option = option.split("/")
        srch = self.__options
        for i in option:
            if i not in srch or not srch[i]:
                return False
            elif srch[i] == True:  # tuples evaluate to True
                return True
            else:
                srch = srch[i]

        return True

    def __parse_options(self, options):
        t = {}
        for i in options:
            if type(i) == types.StringType:
                t[i] = True
            elif type(i) in (types.TupleType, types.ListType):
                if type(i[1]) == types.BooleanType:
                    t[i[0]] = i[1]
                elif type(i[1]) in (types.TupleType, types.ListType):
                    t[i[0]] = f(i[1])

        return t

    def __getitem__(self, key):
        """Get a key from the dictionary.

        @param key: The key
        @type key: C{string}

        """
        return self.__info[key]

    def __setitem__(self, key, value):
        """Set a key in the dictionary.

        @param key: The key
        @type key: C{string}
        @param value: The value
        @type value: C{string}

        """
        self.__info[key] = value

    def __delitem__(self, key):
        """Delete a key from the dictionary.

        @param key: The key
        @type key: C{string}

        """
        del self.__info[key]

    def keys(self):
        """Return a list of keys from the dictionary.

        """
        return self.__info.keys()

    def __contains__(self, key):
        """Return True if the dictionary contains the key, False otherwise.

        @param key: The key
        @type key: C{string}

        """
        return key in self.__info


class Applet(awn.AppletSimple, object):

    def __init__(self, uid, orient, offset, size, meta={}, options=[]):
        """Create a new instance of the Applet object.

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
        awn.AppletSimple.__init__(self, uid, orient, offset, size)

        self.uid = uid

        # Create all required child-objects, others will be lazy-loaded
        self.meta = Meta(self, meta, options)
        self.icon = Icon(self)
        self.tooltip = Title(self)
        self.settings = Settings(self)

        # Dialogs depends on settings
        self.dialog = Dialogs(self)

        if "Applet" in _globalRegister:
            _globalRegister["Applet"].append(self)
        else:
            _globalRegister["Applet"] = [self]

    def connect_size_changed(self, callback):
        self.connect("size-changed", lambda w, e: callback())

    def __getmodule(module):
        """Return a getter that lazy-loads a module, represented by a
        single instantiated class.

        @param module: The class of the module to initialize and get
        @type module: C{class}

        """
        instance = {}

        def getter(self):
            if module not in instance:
                instance[module] = module(self)
            return instance[module]
        return property(getter)

    timing = __getmodule(Timing)
    errors = __getmodule(Errors)
    keyring = __getmodule(Keyring)
    notify = __getmodule(Notify)
    effects = __getmodule(Effects)


def init_start(applet_class, meta={}, options=[]):
    """Do the work to create a new applet, and then start the applet.
    This makes the icon appear on the bar and starts GTK+.

    The callable applet_class parameter is called and given an instance of
    C{Applet}. It can then set an icon, title, dialogs, and other things,
    before GTK+ starts, which makes the icon appear on the AWN panel.

    @param applet_class A callable, used to do some initialization
    @type applet_class: C{callable}
    @param meta: The meta-information to pass to the constructor
    @type meta: C{dict}
    @param options: Options to set for the new applet
    @type options: C{list} or C{tuple}
    @return: The newly created applet.
    @rtype: L{Applet}

    """
    assert callable(applet_class)

    gobject.threads_init()

    awn.init(sys.argv[1:])
    applet = Applet(awn.uid, awn.orient, awn.offset, awn.size, meta, options)
    awn.init_applet(applet)

    try:
        applet_class(applet)
    except Exception, e:
        applet.icon.theme("dialog-error")
        import traceback
        traceback = traceback.format_exception(type(e), e, sys.exc_traceback)
        def crash_applet(widget=None, event=None):
            gtk.main_quit()
        applet.connect("button-press-event", crash_applet)
        applet.errors.general(e, traceback=traceback, callback=crash_applet)

    applet.show_all()
    gtk.main()
