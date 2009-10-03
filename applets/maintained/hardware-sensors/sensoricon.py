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

theme_dir = os.path.join(os.path.dirname(__file__), "themes")

class SensorIcon():

    def __init__(self, theme, sensors, height):
        """
        Initialize icon.
        
        Load icon background, create cairo context and render background.
            theme: icon theme
            sensors: list of sensors who's values are shown in this icon
            height: applet height in pixels
        
        """
        if len(sensors) is 1:
            self.__type = "single"
        else:
            self.__type = "double"

        self.__theme = theme
        self.__sensors = sensors[:2]
        self.__height = height

        self.create_background()

    def theme(self, theme):
        self.__theme = theme
        self.create_background()

    def type(self, type):
        self.__type = type
        self.create_background()

    def set_height(self, height):
        """Set icon height."""
        self.__height = height
        self.create_background()

    def set_sensors(self, sensors):
        """Set sensors who's values are shown in this icon."""
        self.__sensors = sensors[:2]

    def create_background(self):
        filename = os.path.join(theme_dir, self.__theme, self.__type + ".svg")
        background = rsvg.Handle(filename)

        self.__background_surface = cairo.ImageSurface(
                             cairo.FORMAT_ARGB32, self.__height, self.__height)
        background_context = cairo.Context(self.__background_surface)

        svg_width, svg_height = map(float, background.get_dimension_data()[:2])
        background_context.scale(
                         self.__height / svg_width, self.__height / svg_height)

        background.render_cairo(background_context)

    def get_icon(self):
        """Return the applet icon as Cairo context."""

        height = width = self.__height

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, height, height)
        context = cairo.Context(surface)

        context.set_operator(cairo.OPERATOR_OVER)
        # Draw the background image
        context.set_source_surface(self.__background_surface)
        context.paint()

        single = len(self.__sensors) is 1

        for idx, sensor in enumerate(self.__sensors):
            low_value = sensor.low_value
            high_value = sensor.high_value

            context.save()

            # Draw the meter hand
            (red, green, blue, alpha) = sensor.hand_color
            context.set_source_rgba(
                                 float(red) / 65535, float(green) / 65535,
                                 float(blue) / 65535, float(alpha) / 65535)

            # prevent division by zero
            if (high_value - low_value) == 0:
                angle = 0
            else:
                if single:
                    angle = math.pi * (-0.25 + 0.5 *
                     (sensor.value - low_value) / (high_value - low_value))
                else:
                    angle = math.pi * (-0.15 + 0.3 *
                     (sensor.value - low_value) / (high_value - low_value))

            # Move hand to center
            if single:
                context.translate(width / 2, height / 2)
            else:
                context.translate((0.297 + idx * 0.406) * width,
                                  0.539 * height)
            # Rotate the hand
            context.rotate(angle)

            # Draw hand
            y = -height / 2 + 5 if single else (-0.406) * height

            context.move_to(0, y)
            context.line_to(-2, 0)
            context.line_to(0, 5)
            context.line_to(2, 0)
            context.line_to(0, y)
            context.fill()

            # Turn the mask back to the originale state (before translation
            # and rotation)
            context.restore()

        return context
