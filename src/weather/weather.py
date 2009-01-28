#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007, 2008:
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is a weather applet for Avant Window Navigator.
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

from awn.extras import AWNLib
import gtk, cairo, gobject
import urllib2, urllib, re, time, sys, traceback
from xml.dom import minidom

# import socket to set the default timeout, it is unlimited by default!
TIMEOUT_RETRY = 5 # how many minutes in the future to retry, on a timeout
SOCKET_TIMEOUT = 20 # how many seconds to allow a network operation to succeed
import socket
socket.setdefaulttimeout(SOCKET_TIMEOUT)

from helpers import debug, initGetText
#initialize localization, must be done before local imports
initGetText("awn-weather-applet")
import weathericons, forecast, weatherprefs

class WeatherApplet:
    def __init__(self, applet):
        self.applet = applet
        self.cachedConditions = None
        self.iconPixBuf = self.mapPixBuf = None
        self.forecaster = forecast.Forecast(self)
        self.onRefreshForecast = self.forecaster.onRefreshForecast # <3 python
        
        # handle the persisted settings (such as gconf)
        self.fetchSettings()
        ##self.applet.settings.notify("weather", self.onSettingsChanged)
        
        # set default icons/titles/dialogs so the applet is informative without data
        self.setIcon() # initialize the default weather.com icon
        self.applet.title.set("%s %s..."%(_("Fetching conditions for"), self.settingsDict['location']))
        self.createMapDialog() # create the initial map dialog (no map, of course)
        self.createContextMenu() # create the right click menu
        
        # set up the timers which will refresh the conditions, forecast, and weather map
        self.applet.timing.register(self.onRefreshConditions, self.settingsDict['frequency']*60)
        self.applet.timing.register(self.onRefreshForecast, self.settingsDict['frequency_5day']*60)
        self.applet.timing.register(self.onRefreshMap, self.settingsDict['frequency_map']*60)

        # bind to some events we are concerned about
        self.applet.connect("leave-notify-event", self.onMouseOut)
        self.applet.connect("height-changed", self.onBarHeightChange)
        
        # first, get the current conditions, so we can display the icon
        gobject.timeout_add(1500, self.fetchInitialConditions)
        # get everything else in a few seconds, the applet icon is done, let's not hold things up
        gobject.timeout_add(5000, self.fetchInitialData)
        
    def fetchSettings(self, push=True):
        """
        Synchronize the default settings with existing settings (such as gconf).
        If "push" is true, push any non-existent keys out to the system.
        """
        # create our settings dictionary with default values
        self.settingsDict = {
            'temp_position':        0,
            'temp_fontsize':        32.0,
            'metric':               False,
            'curved_dialog':        False,
            'location':             'Portland, ME', # mosburger's hometown :)
            'location_code':        'USME0328',
            'frequency':            30,
            'frequency_map':        30,
            'frequency_5day':       30,
            'map_maxwidth':         450,
            'open_til_clicked':     True,
            }
            
        # first, tell AWNLib which applet we are
        self.applet.settings.cd("weather")
        
        # now, iterate over all of our settings and update them
        for settingKey in self.settingsDict:
            if settingKey in self.applet.settings: # if it exists, update ours
                self.settingsDict[settingKey] = self.applet.settings[settingKey]
            elif push: # otherwise, push our default
                self.applet.settings[settingKey] = self.settingsDict[settingKey]
                
    def onSettingsChanged(self):
        """
        This method grabs the new settings and compares them to the old ones.
        Based on what changed, it updates no less and no more than it needs to.
        """
        oldSettings = self.settingsDict.copy()
        self.fetchSettings(push=False) # don't push any non-existent keys, we already did that
        changedKeys = [key for key in oldSettings if key in self.settingsDict and self.settingsDict[key] != oldSettings[key]]
                
        if 'location_code' in changedKeys: # none of our data is valid!
            # we need to get everything, all other key changes will be handled as a result
            self.onClickRefreshData()
        else: # okay, we don't need to refresh EVERYTHING
            if 'metric' in changedKeys:
                # update everything but that map, that's fine
                self.onRefreshConditions()
                self.onRefreshForecast()
            else: # all the internal data we have is fine, but do we need to display it differently?
                if any([key for key in ['temp_position', 'temp_fontsize'] if key in changedKeys]):
                    # we just need to refresh the icon
                    self.setIcon(self.cachedConditions['CODE'])
                if 'map_maxwidth' in changedKeys:
                    # just recreate the dialog, to resize the (potentially) existing pixbuf
                    self.createMapDialog()
                if 'curved_dialog' in changedKeys:
                    # just recreate the forecast dialog from the existing data
                    self.forecaster.createForecastDialog()
                    
            #TODO: update timer frequencies somehow, so an applet restart isn't required

    def onMouseOut(self, widget, event):
        """
        Hide the dialogs if it is appropriate to do so.
        """
        if self.settingsDict['open_til_clicked'] == False:
            if hasattr(self.forecaster, 'forecastDialog'):
                #self.forecaster.forecastDialog.hide()
                self.applet.dialog.hide()

    def onBarHeightChange(self, widget, event):
        """
        Redraw the applet icon if the bar height changes,
        so that it doesn't look bad. It is automatically
        scaled but this is not good enough to look good.
        """
        self.setIcon(self.cachedConditions['CODE'])
        return False
                
    def createContextMenu(self):
        """
        Build the right-click context menu for this applet.
        """
        menu = self.applet.dialog.menu
        # create the menu items
        refreshItem = gtk.ImageMenuItem(stock_id=gtk.STOCK_REFRESH)
        prefsItem = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        sepItem = gtk.SeparatorMenuItem()
        # add them to the menu
        for item in [refreshItem, prefsItem, sepItem]:
            menu.insert(item, len(menu)-1)
            item.show()
        # attach callbacks
        refreshItem.connect_object("activate", self.onClickRefreshData, "refresh")
        prefsItem.connect_object("activate", self.onClickPreferences, "preferences")
   
    def onClickRefreshData(self, message=None):
        """
        Refresh the icon, forecast, and map data.
        Called by the right-click "Refresh" option.
        """
        self.onRefreshConditions()
        self.onRefreshForecast()
        self.onRefreshMap()
        
    def onClickPreferences(self, message=None):
        """
        Creates and shows the Preferences dialog.
        Called by the right-click "Preferences" option.
        """
        window = weatherprefs.WeatherConfig(self).get_toplevel()
        #window.set_size_request(500, 350)
        window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        window.set_destroy_with_parent(True)
        icon = gtk.gdk.pixbuf_new_from_file(weathericons.GetIcon("44"))
        window.set_icon(icon)
        window.show_all()
        
    def getAttributes(self):
        """
        Return a list of commonly needed items to other modules (such as forecast).
        """
        return self.settingsDict['location_code'], self.settingsDict['metric'], self.cachedConditions
        
    def fetchInitialConditions(self):
        """
        This is called in the init (well, a second after) to
        grab the initial conditions and set the icon.
        """
        #debug("Fetching initial conditions...")
        result = self.onRefreshConditions()
        if result is None:
            debug("Failed fetching initial conditions, trying again in %i minutes"%(TIMEOUT_RETRY))
            # we couldn't get the conditions, try again soon
            gobject.timeout_add(TIMEOUT_RETRY*1000*60, self.fetchInitialConditions)
        return False # stop this timer, we just needed it once
        
    def fetchInitialData(self):
        """
        This function is called to grab the forecast and map data
        when the applet is initialized.
        """
        self.onRefreshForecast()
        self.onRefreshMap()
        return False # stop this timer, we just needed it once
            
    def overlayTemperature(self, iconFile):
        """
        Given a PNG icon, overlay the temperature onto it, and
        return the resulting surface.
        """
        try:
            cs = cairo.ImageSurface.create_from_png(iconFile)
            ct = cairo.Context(cs)
            ct.set_source_surface(cs)
            ct.paint()
            degreesText = self.cachedConditions['TEMP'] + u"\u00B0"
            pngHeight, pngWidth = cs.get_height(), cs.get_width()
            texthPad, textvPad = 11, 3 # distance from sides
            ct.select_font_face("Deja Vu",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
            ct.set_font_size(self.settingsDict['temp_fontsize'])
            textWidth, textHeight = self.getTextSize(ct, degreesText)
            
            # calculate the temperature overlay position
            tempPos = self.settingsDict['temp_position']
            if tempPos in range(6): # 6/7 signifies not to show the temp overlay
                if tempPos in (0,1,2): # bottom
                    # note temp_y is the y pos of the BOTTOM of the text
                    temp_y = pngHeight - textvPad
                else: # top
                    temp_y = textHeight + textvPad
                if tempPos == 0 or tempPos == 3: # align horiz. center
                    # ignore the degree symbol when centering, or it looks wrong
                    temp_x = pngWidth/2 - (textWidth-self.getTextSize(ct, u"\u00B0")[0])/2
                if tempPos == 1 or tempPos == 4: # align left
                    temp_x = texthPad
                if tempPos == 2 or tempPos == 5: # align right
                    temp_x = pngWidth - textWidth - texthPad
                    
                # Draw black temperature text shadow (underneath, so draw first)
                ct.set_line_width(1)
                ct.stroke()
                ct.move_to(temp_x+2,temp_y+2)
                ct.set_source_rgba(0.2,0.2,0.2,.8)
                ct.select_font_face("Deja Vu",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
                ct.show_text(degreesText)
                # Draw white temperature text (draw overtop of "shadow")
                ct.move_to(temp_x,temp_y)
                ct.set_source_rgb(1,1,1)
                ct.select_font_face("Deja Vu",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
                ct.show_text(degreesText)
            return ct.get_target()
                
        except:
            debug("Unexpected error: ");traceback.print_exc()
        
    def setIcon(self, hint='twc'):
        """
        Given a hint correspoding to the codes in weathericons.py, this
        method will grab the image and set it as the icon.
        """
        # grab the appropriate icon
        iconFile = weathericons.GetIcon(hint)

        if hint == 'twc': # if it is just the logo we are done!
            self.applet.icon.file(iconFile)
        else: # otherwise, we overlay the temperature text
            surface = self.overlayTemperature(iconFile)
            if surface is not None: # None is returned on error
                # don't use AWNLib's built in setting and resizing, it needs to be raw because
                # in the case of a bar resize, our event is called first and AWNLib has the old size.
                self.iconPixBuf = self.applet.icon.surface(surface, self.iconPixBuf, set=False)
                height = self.applet.get_height()
                scaledIcon = self.iconPixBuf.scale_simple(height, height, gtk.gdk.INTERP_HYPER)
                self.applet.icon.set(scaledIcon, raw=True)
                
    def getTextSize(self, context, text):
        """
        Return the width and height of a string in pixels,
        if it were to be drawn on the given context.
        """
        return context.text_extents(text)[2:4]
        
    def onRefreshConditions(self):
        """
        Download the current weather conditions. If this fails, or the conditions
        are unchanged, don't do anything. If we get new conditions, update the
        cached conditions and update the applet title and icon.
        """
        #debug("Refreshing CONDITIONS @ %s"%time.asctime())
        conditions = self.fetchConditions()
        if conditions is not None:
            if conditions != self.cachedConditions:
                # mosburger: Weather.com's TOS state that I'm not supposed to change their text. However, I asked them, and
                #   they do not supply non-English weather descriptions. If the current locale uses an English language, they
                #   won't be changed, but otherwise they will.
                # mrooney: I think there is an important difference between 'changing' and 'translating', the latter being
                #   what we are doing. Is this really a TOS violation?
                #TODO: figure out where the gettext wrapping belongs, should we use weathertext?
                title = "%s: %s, %s"%(conditions['CITY'], _(conditions['DESCRIPTION']), conditions['TEMP']+u"\u00B0")
                #display the "Feels Like" temperature in parens, if it is different from the actual temperature
                if conditions['TEMP'] != conditions['FEELSLIKE']:
                    title += " (%s)"%(conditions['FEELSLIKE']+u"\u00B0")
                self.applet.title.set(title)
                self.cachedConditions = conditions
                self.setIcon(conditions['CODE'])
        return conditions
                
    def dictFromXML(self, rootNode, keys, paths):
        """
        Given an XML node, iterate over keys and paths, grabbing the value from each path
        and putting it into the dictionary as the given key.
        """
        returnDict = {}
        for key, path in zip(keys, paths):
            items = path.split('/')
            cnode = rootNode
            for item in items:
                cnode = cnode.getElementsByTagName(item)[0]
            returnDict[key] = ''.join([node.data for node in cnode.childNodes if node.nodeType == node.TEXT_NODE])
        return returnDict
                
    def fetchConditions(self):
        """
        Use weather.com's XML service to fetch the current conditions and return them.
        """
        url = 'http://xoap.weather.com/weather/local/' + self.settingsDict['location_code'] + '?cc=*&prod=xoap&par=1048871467&key=12daac2f3a67cb39&link=xoap'
        if self.settingsDict['metric']:
            url = url + '&unit=m'
            
        try:
            usock = urllib2.urlopen(url)
            xmldoc = minidom.parse(usock)
            usock.close()
            
            names=['CITY','SUNRISE','SUNSET','DESCRIPTION','CODE','TEMP','FEELSLIKE','BAR','BARDESC','WINDSPEED','WINDGUST','WINDDIR','HUMIDITY','MOONPHASE']
            paths=['weather/loc/dnam','sunr','suns','cc/t','cc/icon','cc/tmp','cc/flik','cc/bar/r','cc/bar/d','cc/wind/s','cc/wind/gust','cc/wind/d','cc/hmid','cc/moon/t']
            conditions = self.dictFromXML(xmldoc, names, paths)
            
        except:
            debug("Unexpected error while fetching conditions:"); traceback.print_exc()
            conditions = None
            
        return conditions
        
    def onRefreshMap(self):
        """
        Download the latest map and create a dialog with the new map.
        """
        #debug("Refreshing MAP @ %s"%time.asctime())
        self.fetchMap()
        self.createMapDialog()
        
    def fetchMap(self):
        """
        Download the latest weather map from weather.com, storing it as a pixbuf.
        """
        try:
            page = urllib2.urlopen('http://www.weather.com/outlook/travel/businesstraveler/map/' + self.settingsDict['location_code']).read()
        except:
            debug("Unable to download weather map: "); traceback.print_exc()
        else:
            mapExp = """<IMG NAME="mapImg" SRC="([^\"]+)" WIDTH=([0-9]+) HEIGHT=([0-9]+) BORDER"""
            result = re.findall(mapExp, page)
            if result and len(result) == 1:
                imgSrc, width, height = result[0]
                rawImg = urllib.urlopen(imgSrc)
                pixbufLoader = gtk.gdk.PixbufLoader()
                pixbufLoader.write(rawImg.read())
                self.mapPixBuf = pixbufLoader.get_pixbuf()
                pixbufLoader.close()
                    
    def createMapDialog(self):
        """
        Create a map dialog from the current already-downloaded map image.
        Note that this does not show the dialog, it simply creates it. AWNLib handles the rest.
        """
        dlog = self.applet.dialog.new("secondary")
        if self.mapPixBuf is None: # we don't have a map yet
            dlog.set_title(_("Fetching map..."))
        else: # we have a map, let's put it in the dialog
            dlog.set_title(self.settingsDict['location'])
            map = gtk.image_new_from_pixbuf(self.mapPixBuf)
            mapSize = self.mapPixBuf.get_width(), self.mapPixBuf.get_height()
            
            # resize if necessary as defined by map_maxwidth
            ratio = 1.0 * self.settingsDict['map_maxwidth'] / mapSize[0]
            if ratio < 1:
                newX, newY = [int(ratio*dim) for dim in mapSize]
                pixbuf = map.get_pixbuf()
                scaled = pixbuf.scale_simple(newX, newY, gtk.gdk.INTERP_BILINEAR)
                map.set_from_pixbuf(scaled)

            dlog.add(map)

def main():
    appletInfo = { # used for automatic AWNLib About dialog
        "name": _("Avant Weather Applet"), ##
        "description": _("A Weather Applet for the Avant Window Navigator. Weather data provided by weather.com. Images by Wojciech Grzanka."), ##
        "version" : "0.8.1", ##
        "author": "Mike Desjardins, Mike Rooney", ##
        "copyright-year": "2007-2008", ##
        "logo": weathericons.GetIcon("44"), ##
        "authors": ["Mike Desjardins","Mike Rooney", "Isaac J."], #
        "artists": ["Wojciech Grzanka", "Mike Desjardins"], #
        "email": "mrooney@gmail.com",
        "short": "weather",
        "type": ["Network", "Weather"],
    }
        
    applet = AWNLib.initiate(appletInfo)
    weather = WeatherApplet(applet)
    AWNLib.start(applet)

if __name__ == "__main__":
    main()
