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
import math

import cairo
import rsvg


class SensorIcon():

    def __init__(self, filename, sensors, height):
        """
        Initialize icon.
        
        Load icon background, create cairo context and render background.
            filename: path to background image
            sensors: list of sensors who's values are shown in this icon
            height: icon height in pixels
        
        """
        self.__filename = filename
        self.__sensors = sensors
        self.__height = height

        self.create_background()

    def set_height(self, height):
        """Set icon height."""
        self.__height = height
        self.create_background()

    def set_sensors(self, sensors):
        """Set sensors who's values are shown in this icon."""
        self.__sensors = sensors

    def set_icon_file(self, filename):
        self.__filename = filename
        self.create_background()

    def create_background(self):
        background = rsvg.Handle(self.__filename)
        self.__background_surface = cairo.ImageSurface(
                             cairo.FORMAT_ARGB32, self.__height, self.__height)
        background_context = cairo.Context(self.__background_surface)

        svg_width, svg_height = map(float, background.get_dimension_data()[:2])
        background_context.scale(
                         self.__height / svg_width, self.__height / svg_height)

        background.render_cairo(background_context)

    def get_icon(self):
        """Return the applet icon as Cairo context."""

        values = [sensor.value for sensor in self.__sensors]

        height = width = self.__height

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, height, height)
        context = cairo.Context(surface)

        context.set_operator(cairo.OPERATOR_OVER)
        # Draw the background image
        context.set_source_surface(self.__background_surface)
        context.paint()

        for idx, sensor in enumerate(self.__sensors):

            low_value = sensor.low_value
            high_value = sensor.high_value

            context.save()

            # Draw the meter hand
            context.set_line_width(0.2)
            (red, green, blue, alpha) = sensor.hand_color
            context.set_source_rgba(float(red) / 65535, float(green) / 65535,
                                    float(blue) / 65535, float(alpha) / 65535)

            # prevent division by zero
            if (values[idx] - low_value) == 0:
                angle = -math.pi / 4
            elif (high_value - low_value) == 0:
                angle = 0
            else:
                angle = math.pi * (-0.25 + 0.5 /
                          (high_value - low_value) * (values[idx] - low_value))

            # Move hand to center
            context.translate(width / 2, height / 2)
            # Rotate the hand
            context.rotate(angle)

            # Draw hand
            context.move_to(0, -height / 2)
            context.line_to(-2, 0)
            context.line_to(0, 5)
            context.line_to(2, 0)
            context.line_to(0, -height / 2)
            context.fill()

            # Turn the mask back to the originale state (before translation and
            # rotation)
            context.restore()

        return context
