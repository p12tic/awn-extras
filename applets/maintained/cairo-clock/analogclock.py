# Copyright (C) 2008 - 2009  onox <denkpadje@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math
import os

import pygtk
pygtk.require("2.0")
import gtk

import cairo
import rsvg

cairo_clock_themes_dir = "/usr/share/cairo-clock/themes"
default_themes_dir = os.path.join(os.path.dirname(__file__), "themes")


class AnalogClockThemeProvider:

    """Provides handles of SVG files that are part of the theme.

    The librsvg handles can be used to be rendered to a C{cairo.Context}.

    """

    def __init__(self, theme_name):
        """Load the necessary SVG files of the specified theme.

        """
        self.__theme_name = theme_name

        theme = self.__get_theme_dir(theme_name)
        get_theme = lambda name: rsvg.Handle(os.path.join(theme, name))

        # Background
        self.drop_shadow = get_theme('clock-drop-shadow.svg')
        self.face = get_theme('clock-face.svg')
        self.marks = get_theme('clock-marks.svg')

        # Foreground
        self.face_shadow = get_theme('clock-face-shadow.svg')
        self.glass = get_theme('clock-glass.svg')
        self.frame = get_theme('clock-frame.svg')

        # Shadows of hands
        self.hour_hand_shadow = get_theme('clock-hour-hand-shadow.svg')
        self.minute_hand_shadow = get_theme('clock-minute-hand-shadow.svg')
        self.second_hand_shadow = get_theme('clock-second-hand-shadow.svg')

        # Hands
        self.hour_hand = get_theme('clock-hour-hand.svg')
        self.minute_hand = get_theme('clock-minute-hand.svg')
        self.second_hand = get_theme('clock-second-hand.svg')

    def __get_theme_dir(self, theme):
        theme_dirs = (cairo_clock_themes_dir, default_themes_dir)

        for theme_dir in theme_dirs:
            path = os.path.join(theme_dir, theme)
            if os.path.isdir(path):
                return path

        raise RuntimeError("Did not find path to theme '" + theme + "'")

    def get_name(self):
        return self.__theme_name


class AnalogClock:

    """Used to draw a clock to a C{cairo.Context} using pre-rendered
    Cairo surfaces of the background and foreground of the analog clock.

    Having pre-rendered the background and foreground means those surfaces
    don't have to be rendered everytime a clock is drawn, saving CPU cycles.

    """

    def __init__(self, theme_provider, height):
        """Given a height, create a C{AnalogClock} using the theme
        provided by given provider.

        The base analog clock will contain a background and foreground
        Cairo surface that has been constructed using this theme and height.

        """
        self.__theme = theme_provider

        source_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, height, height)

        self.__background_surface, background_context = self.__create_scaled_surface(source_surface, height)

        # Draw the background of the clock
        self.__theme.drop_shadow.render_cairo(background_context)
        self.__theme.face.render_cairo(background_context)
        self.__theme.marks.render_cairo(background_context)

        self.__foreground_surface, foreground_context = self.__create_scaled_surface(source_surface, height)

        # Draw the foreground of the clock
        self.__theme.face_shadow.render_cairo(foreground_context)
        self.__theme.glass.render_cairo(foreground_context)
        self.__theme.frame.render_cairo(foreground_context)

        del source_surface

    def __create_scaled_surface(self, source_surface, height):
        surface = source_surface.create_similar(cairo.CONTENT_COLOR_ALPHA, height, height)
        context = cairo.Context(surface)

        svg_width, svg_height = map(float, self.__theme.face.get_dimension_data()[:2])
        context.scale(height / svg_width, height / svg_height)

        return surface, context

    def draw_clock(self, context, height, hours, minutes, seconds):
        svg_width, svg_height = map(float, self.__theme.face.get_dimension_data()[:2])

        context.set_operator(cairo.OPERATOR_OVER)

        # Draw the background of the clock
        context.set_source_surface(self.__background_surface)
        context.paint()

        # Scale hands (after painting the background to avoid messing it up)
        context.scale(height / svg_width, height / svg_height)

        context.save()

        context.translate(svg_width / 2, svg_height / 2)

        # Draw the hour hand
        context.save()
        context.rotate((360/12) * (hours+9+(minutes/60.0)) * (math.pi/180))
        self.__theme.hour_hand_shadow.render_cairo(context)
        self.__theme.hour_hand.render_cairo(context)
        context.restore()

        # Draw the minute hand
        context.save()
        context.rotate((360/60) * (minutes+45) * (math.pi/180))
        self.__theme.minute_hand_shadow.render_cairo(context)
        self.__theme.minute_hand.render_cairo(context)
        context.restore()

        # Draw the second hand if configured to do so
        if seconds is not None:
            context.save()
            context.rotate((360/60) * (seconds+45) * (math.pi/180))
            self.__theme.second_hand_shadow.render_cairo(context)
            self.__theme.second_hand.render_cairo(context)
            context.restore()

        context.restore()

        # Don't scale to avoid messing up the foreground
        context.scale(svg_width / height, svg_height / height)

        # Draw foreground of the clock
        context.set_source_surface(self.__foreground_surface)
        context.paint()
