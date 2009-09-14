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

import fileinterface

interface_name = "ACPI"

folders = ["/proc/acpi/thermal", "/proc/acpi/thermal_zone"]
filenames = ["temperature", "status"]


def get_sensors():
    acpisensors = []
    for folder in folders:
        acpisensors += fileinterface.get_sensors_in_path(folder, filenames)
    for sensor in acpisensors:
        sensor.interface = interface_name
    return acpisensors
