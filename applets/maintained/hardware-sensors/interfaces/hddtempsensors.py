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
import socket
import gobject

from sensorinterface import Sensor
from sensorinterface import Updater
from sensorvalues.tempvalue import TempValue

from sensorvalues import units

interface_name = "HDDTemp"
hddtemp_address = ("127.0.0.1", 7634)


class HDDTempSensor(Sensor):

    def __init__(self, name, seq_num, updater):
        Sensor.__init__(self, name, name, TempValue())
        self.__seq_num = seq_num
        self.updater = updater
        self.interface = interface_name

    def read_sensor(self):
        input = self.updater.get_update()
        if input is None:
            return False
        self.value = float(input[3 + 5 * self.__seq_num])
        return True


def get_hddtemp_output():
    try:
        htsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        htsocket.connect(hddtemp_address)
        input = ''
        htin = htsocket.recv(256)
        while len(htin) > 0:
            input = input + htin
            htin = htsocket.recv(256)
        htsocket.close()
    except socket.error, (errno, errorstr):
        print "HDDTemp sensors interface:", \
                                     "Socket error(%s): %s" % (errno, errorstr)
        return None
    if len(input) == 0:
        return None
    return input.split('|')


def get_sensors():
    htsensors = []
    updater = Updater(60, get_hddtemp_output)
    input = get_hddtemp_output()
    if not input:
        return htsensors
    # Number of hdd sensors
    n = (len(input) - 1) / 5
    for i in xrange(0, n):
        new_sensor = HDDTempSensor(input[1 + 5 * i], i, updater)
        new_sensor.label = input[2 + 5 * i]
        unit = input[4 + 5 * i]
        # Set unit
        if unit is 'C':
            new_sensor.unit = units.UNIT_CELSIUS
        elif unit is 'F':
            new_sensor.unit = units.UNIT_FAHRENHEIT
        elif unit is 'K':
            new_sensor.unit = units.UNIT_KELVIN
        else:
            print "HDDTemp sensors interface: unknown unit:", unit
            continue
        htsensors.append(new_sensor)
    return htsensors
