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
import os.path

from sensorinterface import Sensor
from sensorvalues.tempvalue import TempValue

interface_name = "FileInterface"


class FileSensor(Sensor):

    def __init__(self, name, filename):
        Sensor.__init__(self, filename, name, TempValue())
        self.interface = interface_name
        self.__filename = filename

    def read_sensor(self):
        input = self.get_sensor_data()
        if input is None or len(input) < 2:
            return False
        self.value = float(input[-2])
        return True

    def get_sensor_data(self):
        try:
            sensorfile = open(self.__filename, 'r')
        except IOError, (errno, errorstr):
            print "File sensor interface:", \
                                        "I/O error(%s): %s" % (errno, errorstr)
            return None
        input = sensorfile.read().split()
        sensorfile.close()
        return input


def get_sensors_in_path(path, filenames):
    sensors = []
    for root, dirs, files in os.walk(path):
        for file in filter(lambda file: file in filenames, files):
            filename = os.path.join(root, file)
            new_sensor = FileSensor("CPU", filename)
#            input = new_sensor.get_sensor_data()
#            if input is not None:
#                # sensor name string w/o the ':'
#                new_sensor.label = input[0][0:-1]
#                new_sensor.unit = input[2]
            sensors.append(new_sensor)
    return sensors
