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
        hand_color: color of the hand in applet icon for this sensor
        text_color: color of the text in applet icon for this sensor
    
    """
    
    def __init__(self, id, name, sensor_value):
        self.id = id
        self.name = name
        self.label = name
        # Sensor's value, instance of sensor_values.SensorValue
        self.__value = sensor_value
        
        self.show = True
        self.in_icon = False
        self.hand_color = (65535, 0, 0, 65535)
        self.text_color = (65535, 65535, 65535, 65535)
        self.dialog_row = 1024 # Or some other large number :)
        
        self.alarm_on_high = False
        self.alarm_on_low = False
        # whether to trigger the alarm when value exeeds high_value/low_value
        self.__high_alarm_triggered = False
        self.__low_alarm_triggered = False
        
        self.alarm_cb = None
    
    @property
    def value(self):
        """Sensor's current value"""
        return self.__value.value
    
    @value.setter
    def value(self, value):
        self.__value.raw_value = float(value)
        self.check_alarms()
    
    @property
    def low_value(self):
        """Low value bound"""
        return self.__value.low_value
    
    @low_value.setter
    def low_value(self, value):
        self.__value.low_value = value
    
    @property
    def raw_low_value(self):
        """Low value bound (in default unit)"""
        return self.__value.raw_low_value
    
    @raw_low_value.setter
    def raw_low_value(self, value):
        self.__value.raw_low_value = value
    
    @property
    def high_value(self):
        """High value bound"""
        return self.__value.high_value
    
    @high_value.setter
    def high_value(self, value):
        self.__value.high_value = value
    
    @property
    def raw_high_value(self):
        """High value bound (in default unit)"""
        return self.__value.raw_high_value
    
    @raw_high_value.setter
    def raw_high_value(self, value):
        self.__value.raw_high_value = value
    
    @property
    def unit(self):
        """Unit in which the sensor's value is presented"""
        return self.__value.unit
    
    @unit.setter
    def unit(self, unit):
        if self.__value.__class__ is TempValue:
            self.__value.unit = unit
    
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
        self.alarm_cb = alarm_cb
    
    def check_alarms(self):
        # Get value in proper unit
        value = self.__value.value
        
        if self.alarm_on_high:
            # Trigger high alarm, if the alarm is off and the value is above
            # high_value
            if value > self.high_value and not self.__high_alarm_triggered:
                self.__high_alarm_triggered = True
                message = "Warning, %s very high: %i %s" % \
                        (self.label, value, self.get_unit_str())
                        
                # Trigger alarm - call alarm_cb, if it has been set, otherwise
                # print the alarm
                if self.alarm_cb:
                    self.alarm_cb(self, message)
                else:
                    print messages
            
            # Turn of the alarm when value gets 5% bellow high_value
            elif value < self.high_value - 0.05 * abs(self.high_value):
                self.__high_alarm_triggered = False
        
        if self.alarm_on_low:
            # Trigger low alarm, if the alarm is off and the value is bellow
            # low_value
            if value < self.low_value and not self.__low_alarm_triggered:
                self.__low_alarm_triggered = True
                message = "Warning, %s very low: %i %s" % \
                        (self.label, value, self.get_unit_str())
                
                # Trigger alarm - call alarm_cb, if it has been set, otherwise
                # print the alarm
                if self.alarm_cb:
                    self.alarm_cb(self, message)
                else:
                    print message
        
            # If value is above low_value, turn of the alarm
            elif value > self.low_value + 0.05 * abs(self.high_value):
                self.__low_alarm_triggered = False


class Updater():
    """An updater that calls 'callback' function every 'timeout' seconds"""
    
    def __init__(self, timeout, callback):
        self.timeout = timeout - 0.01
        self.get_ouput = callback
        # Time of the last update
        self.last_update = 0
    
    def set_timeout(self, timeout):
        self.timeout = timeout - 0.01
    
    def get_update(self):
        if self.last_update + self.timeout > time.time():
            return self.output
        self.last_update = time.time()
        self.output = self.get_ouput()
        return self.output
