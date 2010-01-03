#!/usr/bin/python
# Copyright (C) 2007, 2008:
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#     Please do not email the above person for support. The 
#     email address is only there for license/copyright purposes.
# Copyright (C) 2009  onox <denkpadje@gmail.com>
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
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import gtk
from gtk import gdk

from awn import Dialog, cairo_rounded_rect, ROUND_ALL
import cairo

from weather import _


class Forecast:

    def __init__(self, parent):
        self.parent = parent
        self.applet = parent.applet
        self.cachedForecast = None

        self.forecastDialog = None
        self.forecastArea = None

    def refresh_forecast(self):
        """Download the current 5-day forecast. If this fails, or the
        forecast is unchanged, don't do anything. If we get a new forecast,
        update the cached information and create an updated dialog.

        """
        def cb(forecast):
            if forecast is not None and forecast != self.cachedForecast:
                self.cachedForecast = forecast

                if self.forecastDialog is None:
                    self.setup_forecast_dialog()
                elif not self.parent.applet.settings['curved_dialog']:
                    self.forecastDialog.set_title("%s %s %s"%(_("Forecast"), _("for"), self.cachedForecast['CITY']))
                self.forecastArea.set_forecast(self.cachedForecast)
        self.parent.fetch_forecast(cb)

    def refresh_unit(self):
        if self.cachedForecast is not None:
            self.forecastArea.set_forecast(self.cachedForecast)

    def setup_forecast_dialog(self):
        """Update the forecast dialog, either a placeholder if no forecast
        data exists, or the desired dialog (curved or normal).

        Note that this does not show the dialog, the dialog themselves handle that.

        """
        if self.cachedForecast is not None:
            if self.forecastDialog is not None:
                del self.forecastDialog
                self.applet.dialog.unregister("main")
            if self.forecastArea is not None:
                del self.forecastArea
    
            if self.parent.applet.settings['curved_dialog']:
                self.forecastDialog = self.CurvedDialogWrapper(self.applet)
                self.applet.dialog.register("main", self.forecastDialog)
                self.forecastArea = CurvedDialog(self.cachedForecast, self.parent)
            else:
                self.forecastDialog = self.applet.dialog.new("main")
                self.forecastDialog.set_title("%s %s %s"%(_("Forecast"), _("for"), self.cachedForecast['CITY']))
                self.forecastArea = NormalDialog(self.cachedForecast, self.parent)
    
            box = gtk.VBox()
            self.forecastArea.set_size_request(450, 160)
            box.pack_start(self.forecastArea, False, False, 0)
            box.show_all()
            self.forecastDialog.add(box)

    class CurvedDialogWrapper(Dialog):

        def __init__(self, applet):
            Dialog.__init__(self, applet)

            self.connect("expose-event", self.expose_event_cb)

        def expose_event_cb(self, widget, event):
            context = widget.window.cairo_create()

            context.set_operator(cairo.OPERATOR_CLEAR)
            context.paint()
            context.set_operator(cairo.OPERATOR_OVER)

            for child in self.get_children():
                self.propagate_expose(child, event)

            return True


class NormalDialog(gtk.Image):

    def __init__(self, forecast, parent_weather):
        gtk.Image.__init__(self)

        self.__parent_weather = parent_weather
        self.set_forecast(forecast)
        self.xPositions = [16, 101, 189, 277, 362]
        self.yPositions = [30, 30, 30, 30, 30]
        self.whiteDayText = False

        self.connect("expose_event", self.expose_event_cb)

    def set_forecast(self, forecast):
        assert forecast is not None
        self.forecast = forecast
        self.__cache_surface = None

    def draw_rounded_rect(self, ct, x, y, w, h):
        cairo_rounded_rect(ct, x, y, w, h, 4, ROUND_ALL)

    def getTextWidth(self, context, text, maxwidth):
        potential_text = text
        text_width = context.text_extents(potential_text.encode('ascii', 'replace'))[2]
        end = -1
        while text_width > maxwidth:
            end -= 1
            potential_text = text.encode('ascii', 'replace')[:end] + '...'
            text_width = context.text_extents(potential_text.encode('ascii', 'replace'))[2]
        return potential_text, text_width

    def drawSingleDay(self, context, x, y, day, text_color):
        high_temp_x = x + 5
        rect_x = x - 3
        rect_y = y + 10
        rect_width = 74
        rect_height = 90
        high_temp_y = rect_y + rect_height - 6
        icon_x = x + 4
        icon_y = rect_y + 2
        context.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        context.save()

        # Rectangle with outline
        context.set_source_rgba(0, 0, 0, 0.85)
        self.draw_rounded_rect(context, rect_x, rect_y, rect_width, rect_height)
        context.fill()
        context.set_line_width(2)
        context.set_source_rgba(0, 0, 0, 0.55)
        self.draw_rounded_rect(context, rect_x, rect_y, rect_width, rect_height)
        context.stroke()

        # Days of the week
        context.set_font_size(12.0)
        context.set_line_width(1)

        day_name = _(day['WEEKDAY'])
        if day == self.forecast['DAYS'][0]:
            day_name = _("Today")
        elif day == self.forecast['DAYS'][1]:
            day_name = _("Tomorrow")

        day_name, day_width = self.getTextWidth(context, _(day_name), 999)
        text_x = rect_x + (rect_width - day_width)/2
        text_y = rect_y - 10

        # Background Day Text
        context.set_source_rgba(0, 0, 0, 0.85)
        self.draw_rounded_rect(context, text_x - 4, text_y - 12, day_width + 8, 16)
        context.fill()

        # White Day Text
        context.move_to(text_x, text_y)
        context.set_source_rgba(1, 1, 1)
        context.show_text(day_name)

        # Icon of condition
        icon_name = self.__parent_weather.get_icon_name(day['CODE'], self.__parent_weather.applet.settings["theme"])
        icon = self.__parent_weather.applet.get_icon().get_icon_at_size(60, icon_name)
        start_x = (rect_width - icon.get_width()) / 2
        start_y = ((high_temp_y - rect_y - 15) - icon.get_height()) / 2
        context.set_source_pixbuf(icon, rect_x + start_x, rect_y + start_y)
        context.fill()
        context.paint()

        # Weather condition
        condition_text = _(day["DESCRIPTION"])
        context.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(9.0)
        context.set_line_width(1)
        condition_text, text_width = self.getTextWidth(context, condition_text, rect_width-5)
        startx = (rect_width - text_width) / 2

        # Text Shadow
        context.set_source_rgba(0.0, 0.0, 0.0)
        context.move_to(rect_x + startx - 1, high_temp_y-15)
        context.show_text(condition_text)

        # Foreground Text
        context.set_source_rgba(1.0, 1.0, 1.0)
        context.move_to(rect_x + startx - 2, high_temp_y-16)
        context.show_text(condition_text)

        # High and Low
        context.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        context.set_font_size(14.0)
        context.set_line_width(1)

        temp_high = self.__parent_weather.convert_temperature(day['HIGH']) + u"\u00B0" if day['HIGH'] != "N/A" else "N/A"
        context.move_to(high_temp_x-3, high_temp_y)
        context.set_source_rgba(1.0, 0.25, 0.25, 1.0)
        context.show_text(temp_high)

        temp_low = self.__parent_weather.convert_temperature(day['LOW']) + u"\u00B0" if day['LOW'] != "N/A" else "N/A"
        context.move_to(high_temp_x+36, high_temp_y)
        context.set_source_rgba(0.5, 0.75, 1.0, 1.0)
        context.show_text(temp_low)

        context.restore()

    def expose_event_cb(self, widget, event):
        context = widget.window.cairo_create()
        context.translate(event.area.x, event.area.y)

        self.draw_days(widget, event, context)
        return False

    def draw_days(self, widget, event, context):
        if self.__cache_surface is None:
            self.__cache_surface = context.get_target().create_similar(cairo.CONTENT_COLOR_ALPHA, event.area.width, event.area.height)
            cache_context = gdk.CairoContext(cairo.Context(self.__cache_surface))
            text_color = widget.get_style().fg[gtk.STATE_PRELIGHT]

            # Draw days
            for xpos, ypos, day in zip(self.xPositions, self.yPositions, self.forecast["DAYS"]):
                self.drawSingleDay(cache_context, xpos, ypos, day, text_color)

            cache_context.set_source_rgb(text_color.red / 65535.0, text_color.green / 65535.0, text_color.blue / 65535.0)
            descStr = _("Weather data provided by weather.com")
            width = cache_context.text_extents(descStr)[2:4][0]
            xpos = event.area.width/2.0 - width/2.0 
            cache_context.move_to(xpos, 145)
            cache_context.show_text(descStr)

        context.set_operator(cairo.OPERATOR_OVER)
        context.set_source_surface(self.__cache_surface)
        context.paint()


class CurvedDialog(NormalDialog):

    def __init__(self, forecast, parent_weather):
        NormalDialog.__init__(self, forecast, parent_weather)

        self.yPositions = [60, 30, 14, 30, 60]
        self.whiteDayText = True

    def expose_event_cb(self, widget, event):
        context = widget.window.cairo_create()

        # first, create a transparent cairo context
        context.set_operator(cairo.OPERATOR_CLEAR)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)

        # then draw the days onto it
        self.draw_days(widget, event, context)
        return True
