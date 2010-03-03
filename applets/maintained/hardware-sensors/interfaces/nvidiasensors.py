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

interface_name = "Nvidia"

try:
    # Parse nvidia-settings output
    regex = r"[^)]*\):\s*(?P<value>[+-]?\d*)\.?\n"
    regexc = re.compile(regex, re.MULTILINE)
except re.error:
    print "Problem initializing nvidiasensors module:\n", \
                                "Unexpected RegEx compilation error:", re.error


class NvSensor(Sensor):

    def __init__(self, idx, updater):
        Sensor.__init__(self, idx, "GPUCoreTemp", TempValue())
        self.updater = updater
        self.interface = interface_name

    def read_sensor(self):
        nv_output = self.updater.get_update()
        if not nv_output or self.id >= len(nv_output):
            self.value = -273
            return False

        line = nv_output[self.id]
        nv_sensor = regexc.match(line)
        if nv_sensor:
            self.value = float(nv_sensor.group("value"))
        else:
            self.value = -273
            return False

        return True


def get_sensors(timeout=1):
    nv_output = get_nvidia_output()
    if not nv_output:
        return []
    updater = Updater(timeout, get_nvidia_output)

    nvsensors = []
    for idx, line in enumerate(nv_output):
        nv_sensor = regexc.match(line)
        if nv_sensor:
            new_sensor = NvSensor(idx, updater)
            nvsensors.append(new_sensor)

    return nvsensors

nvidia_path = '/usr/bin/nvidia-settings'
nvidia_cmd = '/usr/bin/nvidia-settings -q GPUCoreTemp'
##nvcmd = nvidia_path + " -q [gpu:" + str(i) + "]/GPUCoreTemp"

def get_nvidia_output():
    if os.path.exists(nvidia_path):
        try:
            stdout = os.popen(nvidia_cmd)
            nv_output = stdout.readlines()
            stdout.close()
        except:
            print "Problem running", nvidia_cmd, ", please make sure that", \
                                   "nvidia-settings is istalled on you system."
            return None

        if not nv_output or "ERROR" in nv_output:
            return None

        return filter(lambda line: "Attribute" in line, nv_output)

    else:
        return None
