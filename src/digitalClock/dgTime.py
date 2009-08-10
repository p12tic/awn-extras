#
# Copyright Ryan Rushton  ryan@rrdesign.ca
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA

import os
import time

import cairo
import gtk


class dgTime:

    curY = 0
    curX = 0
    shadow_offset = 1

    def __init__(self, prefs, awn):
        self.awn = awn
        self.prefs = prefs
        self.context = None
        self.surface = None
        self.time_string = None
        # doesn't matter what the height is because it will be scaled
        self.height = 48

        def on_map_event(widget, event):
            self.update_clock()
            return True
        self.awn.connect('map-event', on_map_event)
        self.fallback()

    def update_prefs(self, prefs):
        self.prefs = prefs

    def update_clock(self):
        time_string = self.get_time_string()
        if time_string != self.time_string:
            self.time_string = time_string
            self.draw_clock()
        return True

    def reset_width(self):
        if self.prefs['dateBeforeTime']:
            self.width = int(self.height * 2.5)
        else:
            self.width = int(self.height * 1.3)

    def fallback(self):
        icon_theme = gtk.icon_theme_get_default()
        icon = icon_theme.load_icon('awn-applet-digital-clock',
                                    self.height, 0)
        self.awn.set_icon(icon)

    def create_context(self):
        self.reset_width()

        gdk_surface = self.awn.window.cairo_create().get_target()
        if gdk_surface is None:
            self.fallback()
            return
        self.surface = gdk_surface.create_similar(cairo.CONTENT_COLOR_ALPHA,
                                                  self.width, self.height)
        self.context = cairo.Context(self.surface)
        del gdk_surface

    def draw_clock(self):
        self.curY = 0
        self.reset_width()

        if self.prefs['hour12']:
            increase_size = 0
        else:
            increase_size = 1

        if self.context is None:
            self.create_context()
        if self.surface is None or self.context is None:
            self.fallback()
            return
        # clear context
        self.context.set_operator(cairo.OPERATOR_CLEAR)
        self.context.paint()
        self.context.set_operator(cairo.OPERATOR_SOURCE)
        self.context.set_source_surface(self.surface)
        self.context.paint()
        self.context.select_font_face(self.prefs['fontFace'],
                                      cairo.FONT_SLANT_NORMAL,
                                      cairo.FONT_WEIGHT_BOLD)

        if self.prefs['dateBeforeTime']:
            self.draw_text_beside(self.time_string[1], 8, 'd') #Day
            self.draw_text_beside(self.time_string[2], 9.5, 'm') #Month
            # Time
            self.draw_text_beside(self.time_string[0], 4.4 - increase_size,
                                  't')
        else:
            self.draw_text(self.time_string[0], 5 - increase_size) #Time
            self.draw_text(self.time_string[1], 4) #Day
            self.draw_text(self.time_string[2], 4.4) #Month

        self.awn.set_icon_context_scaled(self.context)

    def draw_text(self, text, size):
        size = self.width/size
        self.context.set_font_size(size)
        font_dim = self.get_font_size(text)
        x = (self.width / 2) - (font_dim['width'] / 2)
        # adjust vertical spacing
        v_space = ((self.height / 2.4) - font_dim['height']) / 2.5
        y = self.curY+font_dim['height']+(v_space)
        #Shadow
        self.context.move_to(x + self.shadow_offset, y + self.shadow_offset)
        font_shadow_color = self.prefs['fontShadowColor']
        self.context.set_source_rgba(font_shadow_color.red / 65535.0,
                                     font_shadow_color.green / 65535.0,
                                     font_shadow_color.blue / 65535.0,
                                     0.8)
        self.context.show_text(text)
        #Text
        self.context.move_to(x, y)
        self.context.set_source_rgb(self.prefs['fontColor'].red / 65535.0,
                                    self.prefs['fontColor'].green / 65535.0,
                                    self.prefs['fontColor'].blue / 65535.0)
        self.context.show_text(text)
        self.curY = y

    def draw_text_beside(self, text, size, type):
        if self.curY == 0:
            self.curY = self.height/5
        if type == 't':
            self.width -= (self.curX + 5)
            size = self.width / size
            if self.prefs['hour12']:
                size -= 2
        else:
            size = self.width/size
        self.context.set_font_size(size)
        font_dim = self.get_font_size(text)
        x = 0
        # adjust vertical spacing
        v_space = ((self.height / 2.4) - font_dim['height']) / 1.5
        y = self.curY + font_dim['height'] + v_space
        if type == 't':
            x = self.curX + 5
            y = (self.height / 2) + (font_dim['height'] / 2)
        self.curX = font_dim['width']

        # Shadow
        self.context.move_to(x + self.shadow_offset, y + self.shadow_offset)
        font_shadow_color = self.prefs['fontShadowColor']
        self.context.set_source_rgba(font_shadow_color.red / 65535.0,
                                     font_shadow_color.green / 65535.0,
                                     font_shadow_color.blue / 65535.0,
                                     0.8)
        self.context.show_text(text)
        # Text
        self.context.move_to(x, y)
        self.context.set_source_rgb(self.prefs['fontColor'].red / 65535.0,
                                    self.prefs['fontColor'].green / 65535.0,
                                    self.prefs['fontColor'].blue / 65535.0)
        self.context.show_text(text)
        self.curY = y

    def get_font_size(self, text):
        xbearing, ybearing, width, height, xadvance, yadvance = \
            self.context.text_extents(text)
        if xadvance > width:
            fwidth = xadvance
        else:
            fwidth = width
        return {'width': fwidth, 'height': height}

    def get_time_string(self):
        fullDate = []

        if self.prefs['hour12']:
            fullDate.append(time.strftime('%I:%M %p'))
        else:
            fullDate.append(time.strftime('%H:%M'))
        fullDate.append(time.strftime('%a'))
        fullDate.append(time.strftime('%b %d'))
        return fullDate
