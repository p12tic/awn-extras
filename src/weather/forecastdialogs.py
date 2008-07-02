#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007, 2008:
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#
# This is the forecast dialog for a weather applet for Avant Window Navigator.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import gtk, cairo
from gtk import gdk
import weathericons, weathertext

class NormalDialog(gtk.DrawingArea):
    def __init__(self,forecast):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.onExpose)
        self.forecast = forecast
        self.xPositions = [16, 101, 189, 277, 362]
        self.yPositions = [30 for i in range(5)]
        self.whiteDayText = False

    def drawRoundedRect(self,ct,x,y,w,h,r = 10):
        #   A****BQ
        #  H      C
        #  *      *
        #  G      D
        #   F****E
        ct.move_to(x+r,y)                      # Move to A
        ct.line_to(x+w-r,y)                    # Straight line to B
        ct.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
        ct.line_to(x+w,y+h-r)                  # Move to D
        ct.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
        ct.line_to(x+r,y+h)                    # Line to F
        ct.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
        ct.line_to(x,y+r)                      # Line to H
        ct.curve_to(x,y,x,y,x+r,y)             # Curve to A

    def getTextWidth(self, context, text, maxwidth):
        potential_text = text
        text_width = context.text_extents(potential_text.encode('ascii','replace'))[2]
        end = -1
        while text_width > maxwidth:
            end -= 1
            potential_text = text.encode('ascii','replace')[:end] + '...'
            text_width = context.text_extents(potential_text.encode('ascii','replace'))[2]
        return potential_text, text_width

    def drawSingleDay(self, context, x, y, day):
        high_temp_x = x + 5
        high_temp_y = y + 84
        rect_x = x - 3
        rect_y = y + 5
        rect_width = 74
        rect_height = 86
        icon_x = x + 4
        icon_y = y + 7
        context.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
        context.save()

        ## Rectangle with outline
        context.set_source_rgba (0,0,0,0.85)
        self.drawRoundedRect(context,rect_x,rect_y,rect_width,rect_height)
        context.fill()
        context.set_line_width(2)
        context.set_source_rgba (0,0,0,0.55);
        self.drawRoundedRect(context,rect_x,rect_y,rect_width,rect_height)
        context.stroke()

        ## Days of the week
        context.set_font_size(12.0)
        context.set_line_width(1)

        day_name = _(day['WEEKDAY'])
        if day == self.forecast['DAYS'][0]:
            day_name = _("Today")
        elif day == self.forecast['DAYS'][1]:
            day_name = _("Tomorrow")

        day_name, day_width = self.getTextWidth(context, day_name, 999)
        text_x = rect_x + (rect_width - day_width)/2
        
        # for the curved dialog, we want the text closer to the days
        if self.whiteDayText:
            text_y = rect_y
        else:
            text_y = rect_y - 10

        ## Black Day Text
        context.move_to(text_x, text_y)
        context.set_source_rgba(0.0,0.0,0.0,1.0)
        context.show_text(_(day_name))

        ## White Day Text
        if self.whiteDayText: # draw white text over its "shadow"
            context.move_to(text_x-1, text_y-1)
            context.set_source_rgba(1,1,1)
            context.show_text(_(day_name))

        ## Icon of condition
        icon_name=weathericons.GetIcon(day['CODE'])
        icon = gdk.pixbuf_new_from_file(icon_name)
        scaled = icon.scale_simple(60,60,gdk.INTERP_BILINEAR)
        context.set_source_pixbuf(scaled,icon_x,icon_y)
        context.fill()
        context.paint()

        ## Weather condition
        condition_text = weathertext.conditions[day['CODE']]
        context.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(9.0)
        context.set_line_width(1)
        condition_text, text_width = self.getTextWidth(context, condition_text, rect_width-5)
        startx = (rect_width - text_width) / 2

        ## Text Shadow
        context.set_source_rgba(0.0,0.0,0.0)
        context.move_to(rect_x + startx - 1, high_temp_y-15)
        context.show_text(condition_text)

        # Foreground Text
        context.set_source_rgba(1.0,1.0,1.0)
        context.move_to(rect_x + startx - 2, high_temp_y-16)
        context.show_text(condition_text)

        ## High and Low
        context.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
        context.set_font_size(14.0)
        context.set_line_width(1)
        context.move_to(high_temp_x-3,high_temp_y)
        context.set_source_rgba(1.0,0.25,0.25,1.0)
        context.show_text(day['HIGH'] + u"\u00B0")
        context.move_to(high_temp_x+36,high_temp_y)
        context.set_source_rgba(0.5,0.75,1.0,1.0)
        context.show_text(day['LOW'] + u"\u00B0")
        context.restore()

    def drawDays(self, context):
        for xpos, ypos, day in zip(self.xPositions , self.yPositions, self.forecast['DAYS'] ):
            self.drawSingleDay(context, xpos, ypos, day)

    def onExpose(self, widget, event):
        context = widget.window.cairo_create()
        self.drawDays(context)
        context.set_source_rgb(0.0,0.0,0.0)
        # approximate the location of this string
        descStr = _("Weather data provided by weather.com")
        length = len(descStr)
        xpos = 200 - (length * 10 / 4)
        context.move_to(xpos,145)
        context.show_text(descStr)
        return False


class CurvedDialog(NormalDialog):
    def __init__(self, forecast):
        NormalDialog.__init__(self, forecast)
        self.yPositions = [60, 30, 14, 30, 60]
        self.whiteDayText = True
        
    def onExpose(self, widget, event):
        # first, create a transparent cairo context
        cr = widget.window.cairo_create()
        cr.save()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.restore()
        # then draw the days onto it
        self.drawDays(cr)
        #self.bottom_text(self.context)
        return True

