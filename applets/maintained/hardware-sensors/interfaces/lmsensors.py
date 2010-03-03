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
import re

from sensorinterface import Sensor
from sensorinterface import Updater
from sensorvalues.tempvalue import TempValue
from sensorvalues.voltvalue import VoltValue
from sensorvalues.rpmvalue import RPMValue

interface_name = "LMSensors"

try:
    # Parse lm sensors output
    regex_voltage = r"(?P<label>[^:]*):\s*(?P<value>[+-]?\d+(\.\d*)?)\s*V"
    regex_temp = r"(?P<label>[^:]*):\s*(?P<value>[+-]?\d+(\.\d*)?)\s*.+C"
    regex_fan = r"(?P<label>[^:]*):\s*(?P<value>[+-]?\d+(\.\d*)?)\s*RPM"
    regexc_voltage = re.compile(regex_voltage, re.MULTILINE)
    regexc_temp = re.compile(regex_temp, re.MULTILINE)
    regexc_fan = re.compile(regex_fan, re.MULTILINE)
    regexc = {TempValue: regexc_temp,
              VoltValue: regexc_voltage,
              RPMValue: regexc_fan}
except re.error:
    print "Problem initializing lmsensors module:\n", \
                                "Unexpected RegEx compilation error:", re.error

lmsensors_path = "/usr/bin/sensors"
lmsensors_cmd = lmsensors_path + " -A"


class LmSensor(Sensor):

    def __init__(self, ln, name, sensor_value, updater, double_line):
        Sensor.__init__(self, str(ln) + "_" + name, name, sensor_value)
        self.__line_num = ln
        self.__double_line = double_line
        self.updater = updater
        self.interface = interface_name

    def read_sensor(self):
        lm_output = self.updater.get_update()
        if self.__line_num >= len(lm_output):
            self.value = -273
            return False
        if self.__double_line:
            line = lm_output[self.__line_num - 1] + lm_output[self.__line_num]
        else:
            line = lm_output[self.__line_num]
        sensor = regexc[self.type].match(line)
        if sensor is not None:
            self.value = float(sensor.group("value"))
        else:
            self.value = -273
            return False

        return True


def get_sensors(timeout=1):
    lmsensors = []
    lm_output = get_lmsensors_output()
    if lm_output is None:
        return []
    updater = Updater(timeout, get_lmsensors_output)

    previous_line = None
    for ln, line in enumerate(lm_output):
        double_line = False
        # If the previous line was long, add it to this one
        if previous_line:
            line = previous_line + line
            previous_line = None
            double_line = True
        # Check if the label is longer than 9, in this case the reading is in
        # the next line. In this case the first row ends with ":\n"
        elif line[-2:] == ":\n" and len(line) > 11:
            previous_line = line
            continue

        volt_sensor = regexc_voltage.match(line)
        if volt_sensor is not None:
            name, value = volt_sensor.group("label", "value")
            new_sensor = LmSensor(ln, name, VoltValue(), updater, double_line)
            lmsensors.append(new_sensor)
            continue

        temp_sensor = regexc_temp.match(line)
        if temp_sensor is not None:
            name, value = temp_sensor.group("label", "value")
            new_sensor = LmSensor(ln, name, TempValue(), updater, double_line)
            lmsensors.append(new_sensor)
            continue

        fan_sensor = regexc_fan.match(line)
        if fan_sensor is not None:
            name, value = fan_sensor.group("label", "value")
            new_sensor = LmSensor(ln, name, RPMValue(), updater, double_line)
            lmsensors.append(new_sensor)

    return lmsensors


def get_lmsensors_output():
    if os.path.exists(lmsensors_path):
        try:
            stdout = os.popen(lmsensors_cmd)
            lm_output = stdout.readlines()
            stdout.close()
        except:
            print "Problem running", lmsensors_cmd, \
                ", please make sure that lm-sensors is istalled on you system."
            return None
        return lm_output

    else:
        return None
