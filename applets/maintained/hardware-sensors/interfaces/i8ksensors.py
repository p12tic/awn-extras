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

import os.path

from sensorinterface import Sensor
from sensorinterface import Updater
from sensorvalues.tempvalue import TempValue
from sensorvalues.rpmvalue import RPMValue

i8k_sensors_path = "/proc/i8k"

interface_name = "i8k"

class I8kSensor(Sensor):
    '''
    Sensors from i8kutils
    '''

    def __init__(self, id, name, updater, value):
        Sensor.__init__(self, id, name, value)
        self.updater = updater
        self.interface = interface_name

    def read_sensor(self):
        i8k_output = self.updater.get_update()
        if len(i8k_output) != 10:
            self.value = -273
            return False

        self.value = i8k_output[self.id]
        return True


def get_sensors(timeout=1):
    i8k_output = get_i8kutil_ouput()
    if len(i8k_output) != 10:
        return []

    updater = Updater(timeout, get_i8kutil_ouput)

    try:
        i8k_sensors = []
        # If value is < 0, BIOS is not reporting it, and the value is invalid
        if int(i8k_output[3]) > 0:
            i8k_sensors.append(I8kSensor(3, "CPU temp", updater, TempValue()))
        if int(i8k_output[4]) > 0:
            i8k_sensors.append(I8kSensor(6, "Left fan", updater, RPMValue()))
        if int(i8k_output[5]) > 0:
            i8k_sensors.append(I8kSensor(7, "Right fan", updater, RPMValue()))

        return i8k_sensors
    except ValueError:
        # This happends if one of the above strings is not an int
        return []

def get_i8kutil_ouput():
    """
    Return the content of /proc/i8k in a list of the form:
    
    1.0 A17 2J59L02 52 2 1 8040 6420 1 2
    |   |   |       |  | | |    |    | |
    |   |   |       |  | | |    |    | +------- 10. buttons status
    |   |   |       |  | | |    |    +--------- 9.  ac status
    |   |   |       |  | | |    +-------------- 8.  right fan rpm
    |   |   |       |  | | +------------------- 7.  left fan rpm
    |   |   |       |  | +--------------------- 6.  right fan status
    |   |   |       |  +----------------------- 5.  left fan status
    |   |   |       +-------------------------- 4.  CPU temperature (Celsius)
    |   |   +---------------------------------- 3.  serial number
    |   +-------------------------------------- 2.  BIOS version
    +------------------------------------------ 1.  /proc/i8k format version
    
    A negative value, for example -22, indicates that the BIOS doesn't return
    the corresponding information. This is normal on some models/bioses.
    
    The above was copied from i8kutils' README for convenience
    
    """
    if os.path.exists(i8k_sensors_path):
        try:
            sensorfile = open(i8k_sensors_path, 'r')
        except IOError, (errno, errst):
            print "i8k sensor interface:", "I/O error(%s): %s" % (errno, errst)
            return None
        output = sensorfile.read().split()
        sensorfile.close()
        return output
    else:
        return []
