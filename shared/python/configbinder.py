# Copyright (C) 2009  Michal Hruby <michal.mhr@gmail.com>
# Copyright (C) 2010  onox <denkpadje@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
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

import pygtk
pygtk.require("2.0")
import gtk

import gobject

from desktopagnostic import config, Color
from desktopagnostic.ui import ColorButton


def get_config_binder(client, group, builder=None):

    """Return an object which can be used to set up the bindings and
    then to create a GObject instance. For each binding the given
    desktopagnostic.config.Client instance, group of the key, and
    gtk.Builder instance is used.

    @param client: desktopagnostic.config.Client instance
    @param group: Group of the configuration key
    @param builder: gtk.Builder instance

    """

    class ConfigBinder:

        def __init__(self):
            self.properties = {}
            self.data = {}

        def bind(self, key, widget, *args, **kwargs):
            value = client.get_value(group, key)
            value_type = type(value)
            if value_type in (int, long, float):
                self.properties[key] = (value_type, None, None, gobject.G_MININT, gobject.G_MAXINT, value, gobject.PARAM_READWRITE)
            elif value_type is Color:
                self.properties[key] = (Color.__gtype__, None, None, gobject.PARAM_READWRITE)
            else:
                self.properties[key] = (value_type, None, None, value, gobject.PARAM_READWRITE)
            self.data[key] = (widget, args, kwargs)

        def create_gobject(self):
            super_self = self

            class ConfigGObject(gobject.GObject):

                __gproperties__ = super_self.properties

                def __init__(self):
                    super(ConfigGObject, self).__init__()
                    self.propvalues = dict()
                    for key in super_self.properties:
                        name = key.replace("_", "-")
                        self.propvalues[name] = super_self.properties[key][-2]

                        # Bind to Gtk+ component
                        data = super_self.data[key]
                        widget = builder.get_object(data[0]) if builder is not None else None
                        bind_property(client, group, key, self, name, widget, *data[1], **data[2])

                def do_get_property(self, prop):
                    return self.propvalues[prop.name]

                def do_set_property(self, prop, value):
                    self.propvalues[prop.name] = value

            return ConfigGObject()

    return ConfigBinder()


def bind_property(client, group, key, obj, prop_name, widget=None,
                          read_only=False,
                          getter_transform=None, setter_transform=None,
                          key_callback=None):
    """Bind config key to a property and widget it represents.

    @param client: desktopagnostic.config.Client instance
    @param group: Group of the configuration key
    @param key: Configuration key name
    @param obj: Object to which the configuration key will be bound
    @param prop_name: Property name of the object
    @param widget: Widget which is used to display the setting
    @param read_only: Only load the value from configuration, don't change it
    @param getter_transform: Can be used to transform the config key value
                             to a value accepted by the widget
    @param setter_transform: Can be used to transform the value displayed
                             by widget back to the config key's value type
                             (and/or value range)
    @param key_callback: Callable which will be called when the value of a key
                         has changed

    """
    def get_widget_value(widget):
        # Radio group needs real special case
        if isinstance(widget, gtk.RadioButton):
            # We need to reverse the list, because Gtk+ is smart and uses prepend
            group_widgets = widget.get_group()
            group_widgets.reverse()
            for i in range(len(group_widgets)):
                if group_widgets[i].get_active():
                    return i
            else:
                return -1

        if isinstance(widget, (gtk.CheckButton, gtk.ComboBox)):
            return widget.get_active()
        elif isinstance(widget, (gtk.SpinButton, gtk.Range)):
            return widget.get_value()
        elif isinstance(widget, gtk.FontButton):
            return widget.get_font_name()
        elif isinstance(widget, ColorButton):
            return widget.props.da_color
        elif isinstance(widget, gtk.Entry):
            return widget.get_text()
        else:
            raise NotImplementedError()

    def set_widget_value(widget, value):
        # Radio group needs real special case
        if isinstance(widget, gtk.RadioButton):
            # We need to reverse the list, cause Gtk+ is smart and uses prepend
            group_widgets = widget.get_group()
            group_widgets.reverse()
            for i in range(len(group_widgets)):
                group_widgets[i].set_active(i == value)
            return

        if isinstance(widget, (gtk.CheckButton, gtk.ComboBox)):
            widget.set_active(value)
        elif isinstance(widget, (gtk.SpinButton, gtk.Range)):
            widget.set_value(value)
        elif isinstance(widget, gtk.FontButton):
            return widget.set_font_name(value)
        elif isinstance(widget, ColorButton):
            widget.props.da_color = value
        elif isinstance(widget, gtk.Entry):
            return widget.set_text(value)
        else:
            raise NotImplementedError()

    def get_widget_change_signal_name(widget):
        signal_names = {
            gtk.CheckButton : "toggled",
            gtk.SpinButton  : "value-changed",
            gtk.ComboBox    : "changed",
            gtk.Range       : "value-changed",
            gtk.FontButton  : "font-set",
            ColorButton     : "color-set",
            gtk.Entry       : "changed"
        }
        for cls in signal_names.keys():
            if isinstance(widget, cls):
                return signal_names[cls]
        else:
            raise NotImplementedError()

    def connect_to_widget_changes(widget, callback, data):
        # Radio group needs real special case
        if isinstance(widget, gtk.RadioButton):

            def radio_button_changed(widget, extra):
                if widget.get_active():
                    callback(widget, extra)

            for radio in widget.get_group():
                radio.connect("toggled", radio_button_changed, data)
            return

        signal_name = get_widget_change_signal_name(widget)
        widget.connect(signal_name, callback, data)

    def key_changed(obj, pspec, tuple):
        widget, getter = tuple

        old_value = get_widget_value(widget)
        new_value = obj.get_property(pspec.name)
#        print "(%s) key_changed: property %s changed to %s" % (id(obj), pspec.name, new_value)

        # FIXME: does it need also the widget param?
        if getter is not None:
            new_value = getter(new_value)

        if new_value != old_value:
#            print "(%s) update widget of %s to %s" % (id(obj), widget, new_value)
            set_widget_value(widget, new_value)

    def widget_changed(widget, *args):
        obj, prop_name, setter, key_callback = args[-1]
        new_value = get_widget_value(widget)
#        print "(%s) widget_changed: widget %s changed to %s" % (id(obj), widget, new_value)

        # FIXME: does it need also the widget param?
        if setter is not None:
            new_value = setter(new_value)

        # We shouldn't compare color properties, because they might point
        # to the same instance and would therefore be the same all the time
        if new_value != obj.get_property(prop_name) or isinstance(new_value, Color):
#            print "(%s) update property of %s to %s" % (id(obj), prop_name, new_value)
            obj.set_property(prop_name, new_value)  # update config key

        if key_callback is not None:
            key_callback(new_value)

    value = obj.get_property(prop_name)

    if isinstance(widget, gtk.ComboBox) and type(value) is str:

        def compose(f1, f2):
            def composition(*args, **kwargs):
                return f1(f2(*args, **kwargs))
            return composition

        def getter(prop_value):
            for i, j in enumerate(widget.get_model()):
                if j[0] == prop_value:
                    return i

        def setter(widget_index):
            return widget.get_model()[widget_index][0]

        getter_transform = compose(getter, getter_transform) if getter_transform else getter
        setter_transform = compose(setter_transform, setter) if setter_transform else setter

    # Make sure the widget updates when the prop changes
    obj.connect("notify::" + prop_name, key_changed, (widget, getter_transform))

    # Bind the prop to the config key
    client.bind(group, key, obj, prop_name, read_only, config.BIND_METHOD_FALLBACK)

    # Connect to widget's change signal if we're supposed to update it
    if not read_only and widget is not None:
        data = (obj, prop_name, setter_transform, key_callback)
        connect_to_widget_changes(widget, widget_changed, data)

    # Initialize the widget with the property's value
    if getter_transform is not None:
        value = getter_transform(value)
    set_widget_value(widget, value)
