#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007, 2008:
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This handles forecasts for the weather applet for Avant Window
# Navigator.
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

import gtk, cairo, awn
import urllib2, urllib, re, time, sys, traceback
from xml.dom import minidom
import forecastdialogs, override
from helpers import debug, _

class Forecast:
    def __init__(self, parent):
        self.parent = parent
        self.applet = parent.applet
        self.cachedForecast = None
        self.createForecastDialog()
        
    def onRefreshForecast(self):
        """
        Download the current 5-day forecast. If this fails, or the forecast
        is unchanged, don't do anything. If we get a new forecast, update
        the cached information and create an updated dialog.
        """
        #debug("Refreshing FORECAST @ %s"%time.asctime())
        forecast = self.fetchForecast()
        if forecast is not None and forecast != self.cachedForecast:
            self.cachedForecast = forecast
            self.createForecastDialog()
        
    def fetchForecast(self):
        """
         Use weather.com's XML service to download the latest 5-day forecast.
        """
        locationCode, metric, cachedConditions = self.parent.getAttributes()
        url = 'http://xoap.weather.com/weather/local/' + locationCode + '?dayf=5&prod=xoap&par=1048871467&key=12daac2f3a67cb39&link=xoap'
        if metric:
            url = url + '&unit=m'
            
        try:
            usock = urllib.urlopen(url)
            xmldoc = minidom.parse(usock)
            usock.close()
            
            forecast = {'DAYS':[]}#, 'CITY': cachedConditions['CITY']}
            cityNode = xmldoc.getElementsByTagName('loc')[0].getElementsByTagName('dnam')[0]
            forecast['CITY'] = ''.join([node.data for node in cityNode.childNodes if node.nodeType == node.TEXT_NODE])

            dayNodes = xmldoc.getElementsByTagName('dayf')[0].getElementsByTagName('day')
            for dayNode in dayNodes:
                names = ['HIGH', 'LOW', 'CODE', 'DESCRIPTION', 'PRECIP', 'HUMIDITY', 'WSPEED', 'WDIR', 'WGUST']
                paths = ['hi', 'low', 'part/icon', 'part/t', 'part/ppcp', 'part/hmid', 'part/wind/s', 'part/wind/t', 'part/wind/gust']
                day = self.parent.dictFromXML(dayNode, names, paths)
                day.update({'WEEKDAY': dayNode.getAttribute('t'), 'YEARDAY': dayNode.getAttribute('dt')})
                forecast['DAYS'].append(day)
                
        except:
            debug("Unexpected error while fetching forecast:"); traceback.print_exc()
            forecast = None
            
        return forecast
        
    def createForecastDialog(self):
        """
        Create the forecast dialog, either a placeholder if no forecast data exists,
        or the desired dialog (curved or normal).
        Note that this does not show the dialog, the dialog themselves handle that.
        """
        if hasattr(self, 'forecastDialog'):
            del self.forecastDialog
        
        if self.cachedForecast is None:
            self.forecastDialog = self.applet.dialog.new("main")
            self.forecastDialog.set_title(_("Fetching forecast..."))
        else:
            if self.parent.settingsDict['curved_dialog'] == True:
                self.forecastDialog = override.Dialog(self.applet) #TODO: figure out how to get rid of override
                #self.forecastDialog = awn.AppletDialog(self.applet)
                forecastArea = forecastdialogs.CurvedDialog(self.cachedForecast)
                #TODO: fix incorrect x pos of this dialog if the weather applet moves
            else:
                self.forecastDialog = self.applet.dialog.new("main")
                self.forecastDialog.set_title("%s %s %s"%(_("Forecast"), _("for"), self.cachedForecast['CITY']))
                forecastArea = forecastdialogs.NormalDialog(self.cachedForecast)
            
            box = gtk.VBox()
            forecastArea.set_size_request(450,160)
            box.pack_start(forecastArea, False, False, 0)
            box.show_all()
            self.forecastDialog.add(box)
        
        self.applet.dialog.register("main", self.forecastDialog)
        
    def cropText(self, context, text, maxwidth):
        """
        Given a maximum width, this will crop and ellipsize
        a string as necessary.
        """
        potential_text = text
        text_width = self.getTextSize(context, potential_text)[1]
        end = -1
        while text_width > maxwidth:
            end -= 1
            potential_text = text[:end] + '...'
            text_width = self.getTextSize(context, potential_text)[1]
        return potential_text, text_width
