#!/usr/bin/python
#coding: utf-8
#
#   Copyright 2008-2009 Grega Podlesek <grega.podlesek@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#   MA 02110-1301, USA.

import time
from sensorvalues import units
from sensorvalues.tempvalue import TempValue


class Interface(object):

    def __init__(self):
        pass


class Sensor(object):
    """
    A sensor object with the following attributes:
        id: unique id
        name: sensor's name
        label: a descriptive label
        show: whether to show sensor in main applet dialog or not
        in_icon: whether to show sensor in applet icon or not
    
    """

    def __init__(self, id, name, sensor_value):
        self.id = id
        self.name = name
        self.label = name
        # Sensor's value, instance of sensor_values.SensorValue
        self.__value = sensor_value

        self.show = True
        self.in_icon = False
        self.dialog_row = 1024 # Or some other large number :)

        self.alarm_on_high = False
        self.alarm_on_low = False
        # whether to trigger the alarm when value exeeds high_value/low_value
        self.__high_alarm_triggered = False
        self.__low_alarm_triggered = False

        self.__alarm_cb = None

    def value():
        doc = """Sensor's current value"""

        def fget(self):
            return self.__value.value

        def fset(self, value):
            self.__value.raw_value = float(value)
            self.check_alarms()

        return locals()

    value = property(**value())

    def low_value():
        doc = """Low value bound"""

        def fget(self):
            return self.__value.low_value

        def fset(self, value):
            self.__value.low_value = value

        return locals()

    low_value = property(**low_value())

    def raw_low_value():
        doc = """Low value bound (in default unit)"""

        def fget(self):
            return self.__value.raw_low_value

        def fset(self, value):
            self.__value.raw_low_value = value

        return locals()

    raw_low_value = property(**raw_low_value())

    def high_value():
        doc = """High value bound"""

        def fget(self):
            return self.__value.high_value

        def fset(self, value):
            self.__value.high_value = value

        return locals()

    high_value = property(**high_value())

    def raw_high_value():
        doc = """High value bound (in default unit)"""

        def fget(self):
            return self.__value.raw_high_value

        def fset(self, value):
            self.__value.raw_high_value = value

        return locals()

    raw_high_value = property(**raw_high_value())

    def unit():
        doc = """Unit in which the sensor's value is presented"""

        def fget(self):
            return self.__value.unit

        def fset(self, unit):
            if self.__value.__class__ is TempValue:
                self.__value.unit = unit

        return locals()

    unit = property(**unit())

    @property
    def unit_str(self):
        return units.UNIT_STR[self.unit]

    @property
    def type(self):
        return self.__value.__class__

    def toggle_alarm_on_high(self):
        self.alarm_on_high = not self.alarm_on_high
        self.over_high = False

    def toggle_alarm_on_low(self):
        self.alarm_on_low = not self.alarm_on_low
        self.under_low = False

    def connect_to_alarm(self, alarm_cb):
        self.__alarm_cb = alarm_cb

    def check_alarms(self):
        # Get value in proper unit
        value = self.__value.value

        if self.alarm_on_high:
            # Trigger high alarm, if the alarm is off and the value is above
            # high_value
            if value > self.high_value and not self.__high_alarm_triggered:
                self.__high_alarm_triggered = True
                message = "Warning, %s very high: %i %s" % \
                        (self.label, value, self.unit_str)

                # Trigger alarm - call alarm_cb, if it has been set, otherwise
                # print the alarm
                if self.__alarm_cb:
                    self.__alarm_cb(self, message)
                else:
                    print message

            # Turn of the alarm when value gets 5% bellow high_value
            elif value < self.high_value - 0.05 * abs(self.high_value):
                self.__high_alarm_triggered = False

        if self.alarm_on_low:
            # Trigger low alarm, if the alarm is off and the value is bellow
            # low_value
            if value < self.low_value and not self.__low_alarm_triggered:
                self.__low_alarm_triggered = True
                message = "Warning, %s very low: %i %s" % \
                        (self.label, value, self.unit_str)

                # Trigger alarm - call alarm_cb, if it has been set, otherwise
                # print the alarm
                if self.__alarm_cb:
                    self.__alarm_cb(self, message)
                else:
                    print message

            # If value is above low_value, turn of the alarm
            elif value > self.low_value + 0.05 * abs(self.high_value):
                self.__low_alarm_triggered = False


class Updater():
    """An updater that calls 'callback' function every 'timeout' seconds"""

    def __init__(self, timeout, callback):
        self.__timeout = timeout - 0.01
        self.get_ouput = callback
        # Time of the last update
        self.__last_update = 0

    def set_timeout(self, timeout):
        self.__timeout = timeout - 0.01

    def get_update(self):
        if self.__last_update + self.__timeout > time.time():
            return self.__output
        self.__last_update = time.time()
        # Get updated value by calling the callback
        self.__output = self.get_ouput()
        return self.__output
