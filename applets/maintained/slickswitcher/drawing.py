#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from math import sqrt

import cairo
import pango
import pangocairo
import pygtk
pygtk.require('2.0')
import gtk
import gobject

from desktopagnostic import Color
from desktopagnostic.config import GROUP_DEFAULT

import awn

#Note: I am 99.7% sure I have the definitions of 'viewport' and 'workspace'
#incorrect in this. For now, this only supports Compiz's way of having one
#one viewport in one large workspace. (I may even have that wrong.)

class Drawing(gtk.Table):
    client = None
    background = None
    bg_path = None
    last_width = 0
    last_height = 0
    was_custom = False
    last_mode = ''
    last_file = ''
    last_w = -1
    last_h = -1

    def __init__(self, switch, settings, applet):
        self.switch = switch
        self.settings = settings
        self.applet = applet

        self.awn_client = awn.config_get_default(applet.get_property('panel-id'))
        self.awn_client.notify_add('theme', 'dialog_bg', self.update_color_notify)
        self.awn_client.notify_add('theme', 'border', self.update_color_notify)

        #This class is an inheritance of GtkTable. It deals with the displaying
        #viewports/workspaces, however, it does not do any cairo drawing. It creates
        #a Viewport instance for each viewport, and it draws the border, background,
        #windows, etc.
        #Initiate this widget
        gtk.Table.__init__(self, 1, 1)

        #Get the current number of columns and rows
        #self.update() will use this to see if the layout has changed
        self.num_columns = 0
        self.num_rows = 0

        #List of Viewport widgets
        self.viewport_widgets = []

        #Get the background image as a Cairo surface
        self.update_backgrounds()

        #"Update" the widget, which means checking for layout changes, redrawing
        #all the widgets, etc.
        self.update()

        #Connect to any relevant signal from Wnck
        self.switch.connect(self.update)

        #Update every 2 seconds, starting in 2 seconds
        gobject.timeout_add_seconds(2, self.timeout_update)

    #Get the background image as a surface
    def update_backgrounds(self):
        bgs = self.applet.update_backgrounds(obj=self)
        if bgs is not None:
            self.backgrounds = bgs

    #Update every 2 seconds
    def timeout_update(self):
        self.update_backgrounds()
        self.update()
        return True

    #Update
    def update(self):
        #Get the current number of columns and rows
        num_columns = self.switch.get_num_columns()
        num_rows = self.switch.get_num_rows()

        #Check if the workspace layout has changed
        if num_columns != self.num_columns or num_rows != self.num_rows:
            #Update the number of columns and rows
            self.num_columns, self.num_rows = num_columns, num_rows
            #Remove each Viewport widget from this table. This does not delete it, but
            #it is no longer visible. If necessary, it will be re-added to this table
            for viewport_widget in self.get_children():
                self.remove(viewport_widget)
                viewport_widget.exposed = False

            #It has; get any new Viewport widgets or delete any extras
            num_workspaces = num_columns * num_rows

            #Check if the number of workspaces has increased
            if len(self.viewport_widgets) < num_workspaces:
                #Make as many Viewport widgets as necessary
                for new_viewport in range(num_workspaces - len(self.viewport_widgets)):
                    #Make a new viewport.
                    viewport = ViewportWidget(self)

                    self.viewport_widgets.append(viewport)

            #Check if the number of workspaces has decreased
            if len(self.viewport_widgets) > num_workspaces:

                #Remove as many Viewport widgets a necessary
                for old_viewport in range(len(self.viewport_widgets) - num_workspaces):

                    self.viewport_widgets[-1].destroy()
                    del self.viewport_widgets[-1]

            #Now attach each widget to this table as necessary
            y = 0
            for viewport in self.viewport_widgets:

                #Get which column and row this viewport is in
                row = int(y / float(num_columns)) + 1
                column = int(y % num_columns) + 1

                #Tell this viewport which row, column, and viewport number it is
                viewport.row, viewport.column = row, column
                viewport.number = y+1

                #If this viewport is on the top row, tell it so (rhyme!)
                if row == 1:
                    viewport.top = True
                else:
                    viewport.top = False

                #If this viewport is on the last column (right side), tell it so
                if column == num_columns:
                    viewport.right = True
                else:
                    viewport.right = False

                #If this viewport is on the last row, tell it so (again!)
                if row == num_rows:
                    viewport.bottom = True
                else:
                    viewport.bottom = False

                #If this viewport is on the first column (left side), tell it so
                if column == 1:
                    viewport.left = True
                else:
                    viewport.left = True

                #Attach this Viewport to the table
                self.attach(viewport, column, column + 1, row, row + 1, xpadding=1, \
                    ypadding=1)

                y += 1

        #Update each ViewportWidget
        for viewport in self.viewport_widgets:
            if viewport.exposed == True:
                viewport.expose()

    def update_color(self):
        dialog = self.get_toplevel()

        if self.settings['use_custom']:
            bg_color = Color.from_string('#' + self.settings['custom_back'])
            dialog.set_property('dialog-bg', bg_color)

            border_color = Color.from_string('#' + self.settings['custom_border'])
            dialog.set_property('border', border_color)

        elif self.was_custom:
            bg_color = self.awn_client.get_value('theme', 'dialog_bg')
            dialog.set_property('dialog-bg', bg_color)

            border_color = self.awn_client.get_value('theme', 'border')
            dialog.set_property('border', border_color)

        color = dialog.get_property('dialog-bg')
        self.bg_red = color.get_red() / 65535.0
        self.bg_green = color.get_green() / 65535.0
        self.bg_blue = color.get_blue() / 65535.0
        self.bg_alpha = color.get_alpha() / 65535.0

        self.was_custom = self.settings['use_custom']

    def update_color_notify(self, *args):
        self.update_color()
        self.queue_draw()

class ViewportWidget(gtk.DrawingArea):
    row, column, number = 0, 0, 0
    column = 0
    number = 0
    top = False
    right = False
    bottom = False
    left = False
    last_windows = None
    last_row, last_column, last_number = 0, 0, 0
    last_draw_background = None

    def __init__(self, table):
        self.table = table
        self.settings = table.settings

        #This class is an inheritance of GtkDrawingArea.
        #It gets an instance of the ViewportSurface class, which does the actual
        #drawing. This updates the ViewportSurface when necessary. It is placed
        #appropriately by the 'Drawing' class, which is used directly by the main
        #applet.
        #Initiate this widget
        gtk.DrawingArea.__init__(self)

        #Set up this widget
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.set_size_request(self.settings['width'], self.settings['height'])
        self.exposed = False
        self.connect('expose-event', self.expose)
        self.connect('button-release-event', self.button_release)
        self.connect('enter-notify-event', self.enter_notify)
        self.connect('leave-notify-event', self.leave_notify)

        #Get the background image as a surface or Pixbuf
        self.backgrounds = self.table.backgrounds

        #Get an instance of the ViewportSurface class
        self.surface = ViewportSurface(self)

        #Get whether or not the surface should draw the background color
        self.draw_background = True

    def expose(self, *args):
        windows = self.table.switch.get_windows(self.number)

        #Only update if necessary
        if self.last_windows == windows and self.last_row == self.row and \
            self.last_column == self.column and self.last_number == self.number and \
            self.last_draw_background == self.draw_background:
            #Nothing has changed
            return True

        #Save the values so the above works
        if self.exposed == True:
            self.last_windows = windows
            self.last_row = self.row
            self.last_column = self.column
            self.last_number = self.number

        self.exposed = True

        #Update the values from the table
        self.update_values()

        #Get the colors from the Gtk theme (or the user's custom colors), from
        #the table
        self.bg_red, self.bg_green, self.bg_blue, self.bg_alpha = self.table.bg_red, \
            self.table.bg_green, self.table.bg_blue, self.table.bg_alpha

        #Update the surface
        self.surface.update()

    #The mouse button has been released on this widget
    def button_release(self, widget, event):
        #Only move viewport if not right-clicked
        if event.button != 3:

            #Move the viewport
            self.table.switch.move((self.row - 1, self.column - 1))

            self.table.applet.hide_dialog()

    #The mouse cursor has entered this widget
    def enter_notify(self, widget, event):
        #Make sure that this isn't called too soon
        if self.exposed:

            #Tell the surface that it is hovered over
            self.surface.hovered = True

            #Tell the surface to update
            self.surface.update()

    #The mouse cursor has left this widget
    def leave_notify(self, widget, event):
        #Make sure that this isn't called too soon
        if self.exposed:

            #Tell the surface that it is not hovered over, if it was before
            if self.surface.hovered:
                self.surface.hovered = False

                #Tell the surface to update
                self.surface.update()

    #The ViewportSurface has updated
    def updated(self):
        if self.window is not None:
            cr = self.window.cairo_create()
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.set_source_surface(self.surface.surface, 0, )
            cr.paint()

            del cr

    #Update values from the table
    def update_values(self):
        #Width and height (duh)
        self.set_size_request(self.settings['width'], self.settings['height'])

        #Get whether or not the surface should draw the background color
        self.draw_background = True

        #Get the background image as a surface or Pixbuf
        self.backgrounds = self.table.backgrounds

        #Get whether or not the surface should draw the background color
        self.draw_background = True

class ViewportSurface:
    border = 4
    radius = 13
    line_width = 4.0
    applet_mode = False
    hovered = False
    font_description = pango.FontDescription('sans Semi-Bold Condensed')
    defaults = {}
    defaults['icon_border'] = '000000C0'
    defaults['width'] = 160
    defaults['height'] = 110
    defaults['normal_border'] = 'FFFFFF80'
    defaults['active_border'] = 'FFFFFFFF'
    defaults['window_main'] = 'CCCCCC66'
    defaults['window_border'] = '333333CC'
    defaults['shine_top'] = 'FFFFFF5E'
    defaults['shine_bottom'] = 'FFFFFF3B'
    defaults['shine_hover_top'] = 'FFFFFF80'
    defaults['shine_hover_bottom'] = 'FFFFFF65'
    defaults['text_color'] = 'FFFFFFF3'
    defaults['shadow_color'] = '000000E6'

    def __init__(self, owner, size = None):
        self.owner = owner
        self.settings = owner.settings

        #This class is basically a container for a cairo.ImageSurface, since you
        #can't inherit from a cairo.ImageSurface (for some reason...)
        #It does the drawing on its surface, and tells its owner when it updated

        #Get the height and width for this surface
        if size is not None:
            width, height = size, size
        else:
            width, height = self.settings['width'], self.settings['height']

        #Part of supporting changing the size
        self.last_width, self.last_height = width, height

        #Initiate this
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, \
            height)

    #The owner tells us to update, so do so.
    def update(self, *args):
        #First update values from the owner, such as viewport#, background, etc.
        self.update_values()

        #Check if we have to get a new surface because the size changed
        #Applet mode
        if self.applet_mode:
            if self.last_height != self.height:
                del self.surface

                self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.height, \
                    self.height)

                self.last_width, self.last_height = self.width, self.height
        #Widget mode
        else:
            if self.last_width != self.settings['width'] or self.last_height != \
                self.settings['height']:

                del self.surface

                self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, \
                    self.settings['width'], self.settings['height'])

                self.last_width, self.last_height = self.settings['width'], \
                    self.settings['height']

        #Get a cairo context
        self.cr = pangocairo.CairoContext(cairo.Context(self.surface))

        #Clear the background so it fits in with the dialog (if necessary)
        if self.draw_background:
            self.cr.set_operator(cairo.OPERATOR_SOURCE)
            self.cr.set_source_rgba(self.bg_red, self.bg_green, self.bg_blue, self.bg_alpha)
            self.cr.paint()

        #Clear the background with transparency
        else:
            self.cr.set_operator(cairo.OPERATOR_SOURCE)
            self.cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
            self.cr.paint()

        #Draw with Cairo OVER the surface
        self.cr.set_operator(cairo.OPERATOR_OVER)

        #Draw the rounded border
        self.rounded_border()

        #Clip it and get a new path
        self.cr.clip()
        self.cr.new_path()

        #Fill the rectangle with the background image

        #The background is a GdkPixbuf
        num_bgs = len(self.backgrounds)
        if self.number > num_bgs:
            number = self.number % num_bgs
            if number == 0:
                number = num_bgs
        else:
            number = self.number

        number = number - 1

        if type(self.backgrounds[number]) == gtk.gdk.Pixbuf:
            #Often this gets called while shutting down the applet, and the GdkWindow
            #is None. This should stop some error messages
            if self.owner.window is None:
                return

            #Hooray Gdk!
            gdk_cr = gtk.gdk.CairoContext(self.cr)
            gdk_cr.set_source_pixbuf(self.backgrounds[number], 0, 0)
            gdk_cr.paint()

            del gdk_cr

        #The background is simply a cairo surface
        else:
            self.cr.set_source_surface(self.backgrounds[number], 0, 0)
            self.cr.paint()

        #Draw the windows
        self.draw_windows()

        #Draw the shininess
        self.shine()

        #Draw the number
        self.draw_number()

        #Actually draw the border
        self.rounded_border()
        if self.hovered:
            self.cr.set_source_rgba(*self.active_border)
        elif self.applet_mode:
            self.cr.set_source_rgba(*self.icon_border)
        else:
            self.cr.set_source_rgba(*self.normal_border)
        self.cr.stroke()

        #Tell the owner that we updated
        self.owner.updated()

        #Free some memory
        del self.cr

    #Update the values from the owner
    def update_values(self):
        #Get whether or not we should draw the background color
        self.draw_background = self.owner.draw_background

        #Get the background image as a surface (or Pixbuf)
        self.backgrounds = self.owner.backgrounds

        #Get the background color
        if self.draw_background:
            self.bg_red, self.bg_green, self.bg_blue, self.bg_alpha = self.owner.bg_red, \
                self.owner.bg_green, self.owner.bg_blue, self.owner.bg_alpha

        #Get the height and width for this surface, if in applet mode
        if self.applet_mode:
            self.width, self.height = self.owner.size, self.owner.size

        #Get the user-configurable colors
        self.icon_border = self.get_color('icon_border')
        self.normal_border = self.get_color('normal_border')
        self.active_border = self.get_color('active_border')
        self.shine_top = self.get_color('shine_top')
        self.shine_bottom = self.get_color('shine_bottom')
        self.shine_hover_top = self.get_color('shine_hover_top')
        self.shine_hover_bottom = self.get_color('shine_hover_bottom')
        self.text_color = self.get_color('text_color')
        self.shadow_color = self.get_color('shadow_color')
        self.window_main = self.get_color('window_main')
        self.window_border = self.get_color('window_border')

        #Get the row, column, and viewport# of this viewport
        self.row = self.owner.row
        self.column = self.owner.column
        self.number = self.owner.number

    #Cairo-only functions here

    #Draw shine
    def shine(self):
        self.cr.save()

        #Set the source to a gradient
        if self.hovered:
            top = self.shine_hover_top
            bottom = self.shine_hover_bottom
        else:
            top = self.shine_top
            bottom = self.shine_bottom

        #Figure out the extra space and how far to go down on the left side
        #As an applet icon
        if self.applet_mode:
            space = self.height / 3
            space = space / 2
            further = 8
            y = int(self.height / 6.5) + space
        #As a widget in the dialog
        else:
            space = 0
            further = 16
            y = int(self.settings['height'] / 6.5) + space

        #Get the colors into a gradient
        gradient = cairo.LinearGradient(0.0, 0.0, 0.0, y + further)
        gradient.add_color_stop_rgba(0.0, *top)
        gradient.add_color_stop_rgba(y + (further / 1), *bottom)
        self.cr.set_source(gradient)
        self.cr.fill()

        #Do a bunch of line and math magic
        if self.applet_mode:
            width = self.width
        else:
            width = self.settings['width']

        #Now draw
        self.cr.move_to(0, y + further)
        self.cr.curve_to(width / 3, y + 2, width / 2, y, width, y)
        self.cr.line_to(width, 0)
        self.cr.line_to(0, 0)

        #Finish
        self.cr.close_path()
        self.cr.fill()
        self.cr.stroke()
        self.cr.restore()

    #Draw rounded border
    def rounded_border(self):
        #This function is called multiple times because it draws a path that nothing
        #should go beyond, and the other drawing (windows, background, shine, etc.)
        #will mess up that path, so this is done multiple times, but actually drawn
        #just once

        #Make a new path
        self.cr.new_path()

        #Get the top left and bottom right coordinates
        if self.applet_mode:
            space = self.height / 3
            space = space / 2
            x0 = 0
            y0 = space - 2
            x1 = self.width
            y1 = self.height - space + 2
        else:
            x0 = self.line_width
            y0 = self.line_width
            x1 = self.settings['width'] - self.line_width
            y1 = self.settings['height'] - self.line_width

        #Set the correct line width
        self.cr.set_line_width(self.line_width)

        #Draw the border
        #Copied from Avant Window Navigator and modified for this/ported to python
        #( /libawn/awn-cairo-utils.c )

        #Top left
        self.cr.move_to(x0, y0 + self.radius)
        self.cr.curve_to(x0, y0, x0, y0, x0 + self.radius, y0)

        #Top right
        self.cr.line_to(x1 - self.radius, y0)
        self.cr.curve_to(x1, y0, x1, y0, x1, y0 + self.radius)

        #Bottom right
        self.cr.line_to(x1, y1 - self.radius)
        self.cr.curve_to(x1, y1, x1, y1, x1 - self.radius, y1)

        #Bottom left
        self.cr.line_to(x0 + self.radius, y1)
        self.cr.curve_to(x0, y1, x0, y1, x0, y1 - self.radius)

        #Finish
        self.cr.line_to(x0, y0 + self.radius)
        self.cr.close_path()

    #Draw the number of this viewport
    def draw_number(self):
        if self.settings['use_custom_text']:
            if self.applet_mode:
                self.draw_custom_number(self.owner)

            else:
                self.draw_custom_number(self.owner.table.applet)

        else:
            if not self.applet_mode:
                self.draw_outlined_number(self.owner.table.applet)

    #Draw standard outlined number
    def draw_outlined_number(self, applet):
        size = sqrt(self.settings['width'] ** 2 + self.settings['height'] ** 2)

        self.cr.save()

        props = applet.overlay.props

        try:
            if props.font_mode == 0:
                main_color = props.text_color.get_cairo_color()
                outline_color = [0.0] * 4

            elif props.font_mode == 1:
                main_color = props.text_color.get_cairo_color()
                outline_color = props.text_outline_color.get_cairo_color()

            elif props.font_mode == 2:
                main_color = props.text_outline_color.get_cairo_color()
                outline_color = props.text_color.get_cairo_color()

        except:
            #Use the gtk colors
            style = applet.get_style()
            main_color = Color(style.fg[gtk.STATE_NORMAL], 65535).get_cairo_color()
            outline_color = Color(style.bg[gtk.STATE_NORMAL], 65535).get_cairo_color()

        #Get where the number should go
        x, y = self.settings['width'] / 2, self.settings['height'] / 2
        font_size = 25.0 * (size / 200.0)
        six, eight = (6, 8)

        #Set up the text layout with pango
        layout = self.cr.create_layout()
        self.font_description.set_absolute_size(font_size * pango.SCALE);
        layout.set_font_description(self.font_description)
        layout.set_text(str(self.number));
        w, h = layout.get_pixel_size();

        #Draw the text
        self.cr.move_to(self.settings['width'] / 2 - w / 2, self.settings['height'] / 2 - h / 2)

        self.cr.set_line_width(props.text_outline_width * self.settings['height'] / 120.0);
        self.cr.set_source_rgba(*outline_color)
        self.cr.set_line_join(cairo.LINE_JOIN_ROUND)
        self.cr.layout_path(layout)
        self.cr.stroke_preserve()

        self.cr.set_source_rgba(*main_color)
        self.cr.fill()

        self.cr.restore()

    #Draw classic drop-shadowed number
    def draw_custom_number(self, applet):
        self.cr.save()

        if self.applet_mode:
            size = applet.get_size()
            x, y = self.width / 2, self.height / 2
            font_size = 24.0 * (size / 48.0)
            six = 6 * (size / 48.0)
            eight = 8 * (size / 48.0)

        else:
            size = sqrt(self.settings['width'] ** 2 + self.settings['height'] ** 2)
            x, y = self.settings['width'] / 2, self.settings['height'] / 2
            font_size = 25.0 * (size / 200.0)
            six = 6 * (size / 200.0)
            eight = 8 * (size / 200.0)

        self.cr.select_font_face('Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.cr.set_font_size(font_size)

        #Draw the drop shadow first
        self.cr.move_to(x - six, y + eight)
        self.cr.set_source_rgba(*self.shadow_color)
        self.cr.show_text(str(self.number))

        #Draw the main number second, on top of the drop shadow
        self.cr.set_source_rgba(*self.text_color)
        self.cr.move_to(x - six - 2, y + eight - 2)
        self.cr.show_text(str(self.number))

        self.cr.restore()

    #Draw the windows on this viewport
    def draw_windows(self):

        self.cr.save()

        if self.applet_mode:
            switch = self.owner.switch
        else:
            switch = self.owner.table.switch

        #Get the windows
        windows = switch.get_windows(self.number - 1)

        #Get the size of the screen
        width = switch.width
        height = switch.height

        #Go through each window and draw it
        for window in windows:
            #Get the window's location and size for this smaller size
            tmp_window = []
            if self.applet_mode:
                tmp_window.append(window[0] * self.width / width)
                tmp_window.append(window[1] * self.height / height)
                tmp_window.append(window[2] * self.width / width)
                tmp_window.append(window[3] * self.height / height)
            else:
                tmp_window.append(window[0] * self.settings['width'] / width)
                tmp_window.append(window[1] * self.settings['height'] / height)
                tmp_window.append(window[2] * self.settings['width'] / width)
                tmp_window.append(window[3] * self.settings['height'] / height)

            #Now draw the window (!)

            #Border
            self.rounded_border2(*tmp_window)
            self.cr.set_source_rgba(*self.window_border)
            self.cr.set_line_width(2.0)
            self.cr.stroke()

            #Main part
            self.rounded_border2(*tmp_window)
            self.cr.set_source_rgba(*self.window_main)
            self.cr.fill()

        self.cr.restore()

    #Draw a different rounded border
    def rounded_border2(self, x, y, width, height):
        radius = 7
        #Make a new path
        self.cr.new_path()

        #Get the top left and bottom right coordinates
        x0 = x
        y0 = y
        x1 = x + width
        y1 = y + height

        #Set the correct line width
        self.cr.set_line_width(2.0)

        #Draw the border
        #Copied from Avant Window Navigator and modified for this/ported to python
        #( /libawn/awn-cairo-utils.c )

        #Top left
        self.cr.move_to(x0, y0 + radius)
        self.cr.curve_to(x0, y0, x0, y0, x0 + radius, y0)

        #Top right
        self.cr.line_to(x1 - radius, y0)
        self.cr.curve_to(x1, y0, x1, y0, x1, y0 + radius)

        #Bottom right
        self.cr.line_to(x1, y1 - radius)
        self.cr.curve_to(x1, y1, x1, y1, x1 - radius, y1)

        #Bottom left
        self.cr.line_to(x0 + radius, y1)
        self.cr.curve_to(x0, y1, x0, y1, x0, y1 - radius)

        #Finish
        self.cr.line_to(x0, y0 + radius)
        self.cr.close_path()

    #(Non Cairo)

    #Get a color from AwnConfigClient
    def get_color(self, key):
        s = self.settings[key]
        try:
            assert s is not None
            return self.convert(s)
        except:
            return self.convert(self.defaults[key])

    #Get an integer from AwnConfigClient
    def get_int(self, key):
        i = self.settings[key]
        if i in [None, 0]:
            return self.defaults[key]
        return i

    #Convert 0080FF00 -> [0.0, 0.5, 1.0, 0.0] (note: no #)
    def convert(self, s):
        color = Color.from_string('#' + s)

        return color.get_cairo_color()
