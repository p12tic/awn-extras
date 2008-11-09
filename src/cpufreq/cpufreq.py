#!/usr/bin/python
# Copyright (C) 2008  onox <denkpadje@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import subprocess

import pygtk
pygtk.require('2.0')
import gtk
from gtk import gdk
from gtk import glade
from awn.extras import AWNLib

try:
    import dbus
    import dbus.service
    
    from dbus.mainloop.glib import DBusGMainLoop
except ImportError:
    dbus = None

applet_name = "CPU Frequency Monitor"
applet_version = "0.2.8"
applet_description = "An applet to monitor and control the CPU frequency"

# Themed logo of the applet, used as the applet's icon and shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "cpufreq.svg")

# Interval in seconds between two successive draws of the icon
draw_freq_interval = 0.5

sysfs_dir = "/sys/devices/system/cpu"
proc_cpuinfo_file = "/proc/cpuinfo"

images_dir = os.path.join(os.path.dirname(__file__), "images")

glade_file = os.path.join(os.path.dirname(__file__), "cpufreq.glade")

dbus_bus_name = "org.awnproject.Awn.Applets.CpuFreq"
dbus_object_path = "/org/awnproject/Awn/Applets/CpuFreq"
dbus_object_interface = dbus_bus_name
dbus_object_interface_scaling = dbus_object_interface + ".Scaling"


if dbus is not None:
    try:
        DBusGMainLoop(set_as_default=True)
    except dbus.DBusException:
        dbus = None
    
    class CpuFreqBackendDBusObject(dbus.service.Object):
    
        """A DBus object to read available frequencies and governors, current
        frequency and governor, and to set new frequency or governor.
        
        """
        
        def __init__(self, backend):
            self.__backend = backend
            
            bus = dbus.SessionBus()
            bus.request_name(dbus_bus_name)
            
            dbus.service.Object.__init__(self, bus, dbus_object_path + "/" + str(backend.get_cpu_nr()))
        
        @dbus.service.method(dbus_interface=dbus_object_interface, out_signature="b")
        def SupportsScaling(self):
            return self.__backend.supports_scaling()
        
        @dbus.service.method(dbus_interface=dbus_object_interface, out_signature="i")
        def GetCurrentFrequency(self):
            return self.__backend.get_current_frequency()
        
        @dbus.service.method(dbus_interface=dbus_object_interface, out_signature="ai")
        def GetFrequencies(self):
            return self.__backend.get_frequencies()
        
        @dbus.service.method(dbus_interface=dbus_object_interface_scaling, out_signature="as")
        def GetGovernors(self):
            assert self.__backend.supports_scaling()
            
            return self.__backend.get_governors()
        
        @dbus.service.method(dbus_interface=dbus_object_interface_scaling, out_signature="s")
        def GetCurrentGovernor(self):
            assert self.__backend.supports_scaling()
            
            return self.__backend.get_current_governor()
        
        @dbus.service.method(dbus_interface=dbus_object_interface_scaling, in_signature="i")
        def SetFrequency(self, frequency):
            assert self.__backend.supports_scaling()
            
            return self.__backend.set_frequency(int(frequency))
        
        @dbus.service.method(dbus_interface=dbus_object_interface_scaling, in_signature="s")
        def SetGovernor(self, governor):
            assert self.__backend.supports_scaling()
            
            return self.__backend.set_governor(str(governor))


class CpuFreqApplet:

    """An applet to monitor and control the CPU frequency.
    
    """
    
    __button_press_event_id = None
    
    def __init__(self, applet):
        self.applet = applet
        
        height = self.applet.get_height()
        applet.icon.set(gdk.pixbuf_new_from_file_at_size(applet_logo, height, height))
        
        self.setup_icon()
        
        self.settings = {
            "cpu_number": 0
        }
        applet.settings.load(self.settings)
        
        self.initialize_backend()
        
        self.setup_context_menu()
        
        applet.connect("enter-notify-event", lambda w, e: self.update_title())
        applet.connect("height-changed", self.height_changed_cb)
        
        applet.timing.register(self.draw_freq_cb, draw_freq_interval)
        
        if dbus is not None:
            try:
                CpuFreqBackendDBusObject(self.backend)
            except dbus.DBusException:
                pass
    
    def initialize_backend(self):
        self.backend = None
        for b in backends:
            if b.backend_useable(self.settings["cpu_number"]):
                self.backend = b(self.settings["cpu_number"])
                break
        
        assert self.backend is not None
        
        if self.backend.supports_scaling():
            """
            Compute the difference, R, (in KHz) between the physical maximum and
            minimum frequency. Then, if there are n images, we can split R into n-1
            frequency ranges and map the frequencies in those ranges to the various images
            """
            self.freq_range_per_image = (self.backend.get_phys_max_frequency() - self.backend.get_phys_min_frequency()) / (len(self.icons) - 1)
        
        self.setup_main_dialog()
    
    def height_changed_cb(self, widget, event):
        """Update the applet's icon to reflect the new height.
        
        """
        self.setup_icon()
        
        self.draw_freq_cb()
    
    def setup_icon(self):
        """Load the images that are going to be used as the applet's icon.
        
        """
        height = self.applet.get_height()
        
        self.icons = {}
        for i in range(0, len(os.listdir(images_dir))):
            self.icons[i] = gdk.pixbuf_new_from_file_at_size(os.path.join(images_dir, "cpufreq-" + str(i) + ".svg"), height, height)
    
    def setup_context_menu(self):
        number_of_cpus = self.backend.get_number_of_cpus() # called only once: assumes that every backend returns the same number
        
        if number_of_cpus > 1:
            prefs = glade.XML(glade_file)
            prefs.get_widget("preferences-vbox").reparent(self.applet.dialog.new("preferences").vbox)
            
            combobox = gtk.combo_box_new_text()
            prefs.get_widget("hbox-cpu").add(combobox)
            prefs.get_widget("label-cpu").set_mnemonic_widget(combobox)
            
            for i in range(0, number_of_cpus):
                combobox.append_text(str(i))
            
            combobox.set_active(self.settings["cpu_number"])
            combobox.connect("changed", self.combobox_processor_changed_cb)
    
    def combobox_processor_changed_cb(self, combobox):
        self.applet.settings["cpu_number"] = combobox.get_active()
        
        self.initialize_backend()
    
    def setup_main_dialog(self):
        self.dialog = self.applet.dialog.new("frequency-dialog")
        
        vbox = gtk.VBox()
        self.dialog.add(vbox)

        if self.backend.supports_scaling():
            group = None
            self.radio_buttons = {}
            
            governors = self.backend.get_governors()
            
            if "userspace" in governors:
                governors.remove("userspace")
                
                for i in self.backend.get_frequencies():
                    group = gtk.RadioButton(group, self.human_readable_freqency(i))
                    group.props.can_focus = False
                    vbox.add(group)
                    self.radio_buttons[i] = group
                    group.connect("toggled", self.frequency_changed_cb, i)
                
                vbox.add(gtk.SeparatorMenuItem())
            
            for i in governors:
                group = gtk.RadioButton(group, i)
                group.props.can_focus = False
                vbox.add(group)
                self.radio_buttons[i] = group
                group.connect("toggled", self.governor_changed_cb, i)
        else:
            hbox = gtk.HBox(spacing=6)
            hbox.set_border_width(6)
            vbox.add(hbox)
            
            hbox.add(gtk.image_new_from_icon_name("dialog-information", gtk.ICON_SIZE_DIALOG))
            label = gtk.Label("<span size=\"large\"><b>Scaling unavailable</b></span>\n\nFrequency scaling is not\navailable for the selected CPU.")
            label.set_use_markup(True)
            hbox.add(label)
        
        if self.__button_press_event_id is not None:
            self.applet.disconnect(self.__button_press_event_id)
        self.__button_press_event_id = self.applet.connect("button-press-event", self.button_press_event_cb)
    
    def button_press_event_cb(self, widget, event):
        if event.button == 1:
            if self.backend.supports_scaling() and not self.dialog.is_active():
                governor = self.backend.get_current_governor()
                
                if governor == "userspace":
                    self.radio_buttons[self.backend.get_current_frequency()].set_active(True)
                else:
                    self.radio_buttons[governor].set_active(True)
            
            self.applet.dialog.toggle("frequency-dialog")
    
    def human_readable_freqency(self, frequency):
        frequency = float(frequency)
        
        if frequency >= 1e6:
            divisor = 1e6
            unit = "GHz"
        else:
            divisor = 1e3
            unit = "MHz"
        
        if frequency % divisor == 0:
            ffreq = str(int(frequency / divisor))
        else:
            ffreq = "%3.2f" % (frequency / divisor)
        
        return ffreq + " " + unit
    
    def frequency_changed_cb(self, widget, frequency):
        """Set the governor to 'userspace' and changes the current frequency.
        
        """
        if widget.get_active():
            self.backend.set_frequency(frequency)
            
            self.applet.dialog.toggle("frequency-dialog", "hide")
            self.applet.title.hide()
    
    def governor_changed_cb(self, widget, governor):
        """Change the current governor.
        
        """
        if widget.get_active():
            self.backend.set_governor(governor)
            
            self.applet.dialog.toggle("frequency-dialog", "hide")
            self.applet.title.hide()
    
    def draw_freq_cb(self):
        """Draw the icon and updates the title to keep it synchronized with the drawn frequency.
        
        """
        if self.backend.supports_scaling():
            number = float(self.backend.get_current_frequency() - self.backend.get_phys_min_frequency()) / self.freq_range_per_image
            icon = self.icons[int(round(number))]
        else:
            icon = self.icons[len(self.icons) - 1]
        applet.icon.set(icon, True)
        
        self.update_title()
        
        return True
    
    def update_title(self):
        if not self.applet.title.is_visible():
            return
        
        title = self.human_readable_freqency(self.backend.get_current_frequency())
        
        if self.backend.supports_scaling():
            title = self.backend.get_current_governor() + ": " + title
        
        self.applet.title.set(title)
        self.applet.title.show()


class SysFSBackend:

    """Backend using the syfs filesystem. Requires Linux 2.6 and the
    cpufreq-selector program from gnome-applets.
    
    """
    
    def __init__(self, cpu_nr):
        self.__cpu_nr = cpu_nr
    
    @staticmethod
    def backend_useable(cpu_nr):
        return os.path.isdir(os.path.join(sysfs_dir, "cpu" + str(cpu_nr), "cpufreq"))
    
    def supports_scaling(self):
        return True
    
    def get_cpu_nr(self):
        return self.__cpu_nr
    
    def get_number_of_cpus(self):
        pattern = re.compile("cpu\d")
        return len([i for i in os.listdir(sysfs_dir) if pattern.match(i)])
    
    def get_governors(self):
        return open(os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq/scaling_available_governors")).read().strip().split()
    
    def get_frequencies(self):
        return map(int, open(os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq/scaling_available_frequencies")).read().strip().split())
    
    def set_governor(self, governor):
        assert governor in self.get_governors(), "Governor '" + governor + "' unknown"
        
        subprocess.Popen("cpufreq-selector -c " + str(self.__cpu_nr) + " -g " + governor, shell=True)
    
    def set_frequency(self, frequency):
        assert frequency in self.get_frequencies(), "Frequency " + str(frequency) + " invalid"
        
        self.set_governor("userspace")
        
        subprocess.Popen("cpufreq-selector -c " + str(self.__cpu_nr) + " -f " + str(frequency), shell=True)
    
    def get_current_governor(self):
        return open(os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq/scaling_governor")).read().strip()
    
    def get_current_frequency(self):
        return self.__read_frequency("scaling_cur_freq")
    
    def get_phys_min_frequency(self):
        return self.__read_frequency("cpuinfo_min_freq")
    
    def get_phys_max_frequency(self):
        return self.__read_frequency("cpuinfo_max_freq")
    
    def get_min_frequency(self):
        return self.__read_frequency("scaling_min_freq")
    
    def get_max_frequency(self):
        return self.__read_frequency("scaling_max_freq")
    
    def __read_frequency(self, file):
        return int(open(os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq", file)).read().strip())


class ProcCPUInfoBackend:

    """Backend using /proc/cpuinfo. Does not provide the ability to scale
    the CPU frequency.
    
    """
    
    def __init__(self, cpu_nr):
        self.__cpu_nr = cpu_nr
        self.__cpuinfo_pattern = pattern = re.compile("cpu MHz\s+: (\d+\.\d+)")
    
    @staticmethod
    def backend_useable(cpu_nr):
        if not os.path.isfile(proc_cpuinfo_file):
            return False
        return re.compile("processor\s+: %d" % cpu_nr).search(open(proc_cpuinfo_file).read()) is not None
    
    def supports_scaling(self):
        return False
    
    def get_cpu_nr(self):
        return self.__cpu_nr
    
    def get_number_of_cpus(self):
        file = open(proc_cpuinfo_file).read()
        return len(self.__cpuinfo_pattern.findall(file))
    
    def get_frequencies(self):
        return [self.get_current_frequency()]
    
    def get_current_frequency(self):
        file = open(proc_cpuinfo_file).read()
        # Multiply by 1000 because value is in MHz and should be in KHz
        return int(float(self.__cpuinfo_pattern.findall(file)[self.__cpu_nr])) * 1000


backends = [SysFSBackend, ProcCPUInfoBackend]


if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name, "short": "cpufreq",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": 2008,
        "authors": ["onox <denkpadje@gmail.com>"]},
        ["settings-per-instance"])
    CpuFreqApplet(applet)
    AWNLib.start(applet)