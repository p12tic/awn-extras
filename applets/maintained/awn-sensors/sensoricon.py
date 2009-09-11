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
        self.sensors = sensors
        self.height = height
        
        self.set_icon_file(filename)
    
    def set_height(self, height):
        """Set icon height."""
        self.height = height
    
    def set_sensors(self, sensors):
        """Set sensors who's values are shown in this icon."""
        self.sensors = sensors
    
    def set_icon_file(self, filename):
        background = rsvg.Handle(filename)
        
        self.background_surface = cairo.ImageSurface(
                                 cairo.FORMAT_ARGB32, self.height, self.height)
        background_context = cairo.Context(self.background_surface)

        svg_width, svg_height = map(float, background.get_dimension_data()[:2])
        background_context.scale(
                             self.height / svg_width, self.height / svg_height)
        
        background.render_cairo(background_context)
    
    def get_icon(self):
        """Return the applet icon as Cairo context."""
        
        values = [sensor.value for sensor in self.sensors]
        
        height = width = self.height
        
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, height, height)
        context = cairo.Context(surface)
        
        context.set_operator(cairo.OPERATOR_OVER)
        # Draw the background image
        context.set_source_surface(self.background_surface)
        context.paint()
        
        for idx, sensor in enumerate(self.sensors):
            
            low_value = sensor.low_value
            high_value = sensor.high_value
            
            context.save()
            
            # draw the meter hand
            context.set_line_width(0.2)
            (red, green, blue, alpha) = sensor.hand_color
            context.set_source_rgba(float(red)/65535, float(green)/65535,
                                    float(blue)/65535, float(alpha)/65535)
            # rotate the hand
            angle = math.pi * (-0.25 + 0.5 /
                          (high_value - low_value) * (values[idx] - low_value))
            context.translate(width/2, height/2)
            context.rotate(angle)
            
            # draw hand
            context.move_to(0, -height/2)
            context.line_to(-2, 0)
            context.line_to(0, 5)
            context.line_to(2, 0)
            context.line_to(0, -height/2)
            context.fill()
            
            # Turn the mask back to the originale state (before translation and
            # rotation)
            context.restore()
        
        # == Show text == #
        text_y = height * 6/7
        # Set font
        context.set_font_size(11.0)
        context.select_font_face("Deja Vu",
                                 cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_NORMAL)
        
        # Only one or two values ca be displayed
        text_x_prim, text_x_sec = None, None
        if len(values) == 1:
            value = values[0]
            text_x_prim = width/2 - len(str(value)) * 3.5
        elif len(values) > 1:
            value_prim = values[0]
            value_sec = values[1]
            delta = (len(str(value_prim)) + len(str(value_sec))) * 3.5 + 2
            text_x_prim = width/2 - delta
            delta = delta - len(str(value_prim)) * 7 - 4
            text_x_sec = width/2 - delta
        
        # Show first value
        if (text_x_prim != None):
            # Text Shadow
#                context.move_to(text_x+2,text_y+2)
#                context.set_source_rgba(0,0,0,.8)
#                context.show_text(text)
    
            # Text
            context.move_to(text_x_prim, text_y)
            (red, green, blue, alpha) = self.sensors[0].text_color
            context.set_source_rgba(float(red) / 65535, float(green) / 65535,
                                    float(blue) / 65535, float(alpha) / 65535)
            context.show_text(str(values[0]))
        
        # Show secon value
        if (text_x_sec != None):
            # Text Shadow
#                context.move_to(text_x+2,text_y+2)
#                context.set_source_rgba(0,0,0,.8)
#                context.show_text(text)
    
            # Text
            context.move_to(text_x_sec, text_y)
            (red, green, blue, alpha) = self.sensors[1].text_color
            context.set_source_rgba(float(red) / 65535, float(green) / 65535,
                                    float(blue) / 65535, float(alpha) / 65535)
            context.show_text(str(values[1]))
        
        return context
