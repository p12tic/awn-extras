# Copyright (C) 2010  onox <denkpadje@gmail.com>
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

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras.awnlib import add_cell_renderer_text
from awn.extras.threadqueue import ThreadQueue, async_method
from awn import OverlayThemedIcon

import sun
sun_obj = sun.Sun()

try:
    import pymetar as metar
except ImportError:
    metar = None


class Weather:

    def __init__(self, applet):
        self.__applet = applet

        self.network_handler = NetworkHandler()

        self.__weather_overlay = OverlayThemedIcon(applet.applet.get_icon(), "weather-snow", "weather")

        self.__weather_overlay.props.scale = 0.4
        self.__weather_overlay.props.alpha = 1.0
        self.__weather_overlay.props.gravity = gtk.gdk.GRAVITY_SOUTH_EAST
        self.__weather_overlay.props.apply_effects = False
        self.__weather_overlay.props.active = applet.applet.settings["show-weather"]
        applet.applet.add_overlay(self.__weather_overlay)

    @classmethod
    def plugin_useable(self):
        return metar is not None

    def get_name(self):
        return "Weather"

    def get_element(self):
        return None

    def set_preferences_page_number(self, page_number):
        self.__page_number = page_number

    def get_preferences(self, prefs):
        self.__prefs_tab = WeatherPreferencesTab(prefs, self.__applet.binder, self.__weather_overlay)

        return self.__prefs_tab.get_prefs_widget()
    
    def get_report_fetcher(self, code):
        print "creating report fetcher for %s" % code
        return metar.ReportFetcher(code)

    def refresh_weather(self, report_fetcher, location_cb, city_datetime, get_offset_minutes):
        print "refresh weather!"
        def cb(report):
            print "  callback refresh weather!"
            weather = report.getWeather()
            if weather is not None:
                weather = weather.lower()
            sky = report.getSkyConditions()

            # free identifiers: self.__parent.get_offset_minutes and city_datetime
            hours_offset_utc = get_offset_minutes(city_datetime) / 60
            year = int(city_datetime.strftime("%Y"))
            month = int(city_datetime.strftime("%m"))
            day = int(city_datetime.strftime("%d"))
            hours1 = int(city_datetime.strftime("%H"))
            minutes1 = int(city_datetime.strftime("%M"))
    
            fa = lambda v: v + hours_offset_utc
            fb = lambda v: (int(v), int(round(v % 1 * 60))) 
            srss = map(fb, map(fa, sun_obj.sunRiseSet(year, month, day, report.longf, report.latf)))
    
            print report.stat_city, weather, sky, srss
            if weather is not None and "clouds" in weather:
                if srss[1] <= (hours1, minutes1) or (hours1, minutes1) < srss[0]:
                    image = "weather-few-clouds-night"
                else:
                    image = "weather-few-clouds"
            elif weather is not None and ("fog" in weather or "mist" in weather or "smoke" in weather):
                image = "weather-fog"
            elif sky is None or "clear" in sky:
                if srss[1] <= (hours1, minutes1) or (hours1, minutes1) < srss[0]:
                    image = "weather-clear-night"
                else:
                    image = "weather-clear"
            elif weather == "":
                image = "weather-severe-alert"
            elif "rain" in weather:
                image = "weather-showers"
            elif sky == "overcast":
                image = "weather-overcast"
            elif weather == "":
                image = "weather-showers-scattered"
            elif weather is not None and "snow" in weather:
                image = "weather-snow"
            elif weather == "":
                image = "weather-storm"
            else:
                image = None
            location_cb(weather, sky, srss, image)
        self.network_handler.get_report(report_fetcher, callback=cb)


class WeatherPreferencesTab:

    """Deals with the "Weather" tab in the preferences window of the
    applet.

    """

    def __init__(self, prefs, binder, weather_overlay):
        self.__prefs = prefs
        self.__weather_overlay = weather_overlay

        add_cell_renderer_text(prefs.get_object("combobox-temperature-unit"))
        add_cell_renderer_text(prefs.get_object("combobox-wind-speed-unit"))

        binder.bind("temperature-unit", "combobox-temperature-unit")
        binder.bind("wind-speed-unit", "combobox-wind-speed-unit")
        binder.bind("show-weather", "check-show-weather", key_callback=self.show_weather_toggled_cb)

    def show_weather_toggled_cb(self, value):
        self.__weather_overlay.props.active = value

    def get_prefs_widget(self):
        return self.__prefs.get_object("vbox-weather")


class NetworkException(Exception):
    pass


def network_exception(func):
    def bound_func(obj, *args, **kwargs):
        try:
            return func(obj, *args, **kwargs)
        except IOError, e:
            raise NetworkException("error in %s: %s" % (func.__name__, e))
        except StandardError:
            raise
        except Exception, e:
            raise NetworkException("error in %s: %s" % (func.__name__, e))
    return bound_func


class NetworkHandler(ThreadQueue):

    @async_method
    @network_exception
    def get_report(self, report_fetcher):
        # Fetching the report may take a couple of seconds
        fetched_report = report_fetcher.FetchReport()

        return metar.ReportParser(fetched_report).ParseReport()
