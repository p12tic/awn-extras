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

import os
import time
import re

from sensorinterface import Sensor
from sensorinterface import Updater
from sensorvalues.tempvalue import TempValue
from sensorvalues.voltvalue import VoltValue
from sensorvalues.rpmvalue import RPMValue

from sensorvalues import units

interface_name = "NVClock"

try:
    # Parse lm sensors output
    regex_voltage = r"(?P<label>[^:]*):\s*(?P<value>[+-]?\d+(\.\d*)?)\s*V"
    regex_temp = ur"(?P<label>[^:]*):\s*(?P<value>[+-]?\d+(\.\d*)?)\s*˚?C"
    regex_fan = r"(?P<label>[^:]*):\s*(?P<value>[+-]?\d+(\.\d*)?)\s*RPM"
    regexc = {VoltValue: re.compile(regex_voltage, re.MULTILINE),
              TempValue: re.compile(regex_temp, re.MULTILINE),
              RPMValue: re.compile(regex_fan, re.MULTILINE)}
except re.error:
    print "Problem initializing nvclocksensors module:\n", \
                                "Unexpected RegEx compilation error:", re.error

nvclock_path = "/usr/bin/nvclock"
nvclock_cmd = nvclock_path + " -i"


class NVCoreSensor (Sensor):
    
    def __init__(self, ln, name, sensor_value, updater):
        Sensor.__init__(self, str(ln) + "_" + name, name, sensor_value)
        self.ln = ln
        self.updater = updater
        self.interface = interface_name
    
    def get_updater(self):
        return self.updater
        
    def read_sensor(self):
        nv_output = self.updater.get_update()
        if not nv_output or self.ln >= len(nv_output):
            self.value = -273
            return False
        
        line = nv_output[self.ln]
        sensor = regexc[self.type].match(line)
        if sensor:
            self.value = float(sensor.group("value"))
        else:
            self.value = -273
            return False
        
        return True


def get_sensors(timeout=1):
    nv_output = get_nvclock_output()
    if not nv_output:
        return []
    updater = Updater(timeout, get_nvclock_output)
    
    nvsensors = []
    for ln, line in enumerate(nv_output):
        
        volt_sensor = regexc[VoltValue].match(line)
        if volt_sensor != None:
            name, value = volt_sensor.group("label", "value")
            new_sensor = NVCoreSensor(ln, name, VoltValue(), updater)
            nvsensors.append(new_sensor)
            continue
        
        temp_sensor = regexc[TempValue].match(line)
        if temp_sensor != None:
            name, value = temp_sensor.group("label", "value")
            new_sensor = NVCoreSensor(ln, name, TempValue(), updater)
            nvsensors.append(new_sensor)
            continue
        
        fan_sensor = regexc[RPMValue].match(line)
        if fan_sensor != None:
            name, value = fan_sensor.group("label", "value")
            new_sensor = NVCoreSensor(ln, name, RPMValue(), updater)
            nvsensors.append(new_sensor)
            continue
    
    return nvsensors


def get_nvclock_output():
    if os.path.exists(nvclock_path):
        try:
            stdout = os.popen(nvclock_cmd)
            nv_output = stdout.readlines()
            stdout.close()
        except:
            print "Problem running", nvclock_cmd, \
                   ", please make sure that nvclock is istalled on you system."
            return None
        return nv_output
    else:
        return None
