#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
bandwidth-monitor - Network bandwidth monitor.
Copyright (c) 2006-2009 Kyle L. Huff (kyle.huff@curetheitch.com)
url: <http://www.curetheitch.com/projects/awn-bwm/>
Email: awn-bwm@curetheitch.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
"""

import gtk
import gobject


class preferences:

    def __init__(self, applet, parent):
        self.applet = applet
        self.parent = parent

    def setup(self):
        prefs_ui = gtk.Builder()
        prefs_ui.add_from_file(self.parent.UI_FILE)
        preferences_vbox = self.applet.dialog.new("preferences").vbox
        cell_box = self.create_treeview()
        store = cell_box.liststore
        scaleThresholdSpinbutton = prefs_ui.get_object("scaleThresholdSpinbutton")
        thresholdLabel = prefs_ui.get_object("label-scaleThreshold")
        scaleThresholdSpinbutton.set_value(float(self.applet.settings["draw_threshold"]))
        scaleThresholdSpinbutton.connect('value-changed', self.parent.change_draw_ratio)
        uomCheckbutton = prefs_ui.get_object('uomCheckbutton')
        self.uomCheckbutton = uomCheckbutton
        if self.parent.unit == 1:
            uomCheckbutton.set_property('active', True)
            thresholdLabel.set_text("KBps")
        else:
            thresholdLabel.set_text("Kbps")
        uomCheckbutton.connect('toggled', self.parent.change_unit, scaleThresholdSpinbutton, thresholdLabel)
        graphZerotoggle = prefs_ui.get_object('graphZerotoggle')
        graphZerotoggle_value = True if not self.parent.graph_zero else False
        graphZerotoggle.set_property('active', graphZerotoggle_value)
        graphZerotoggle.connect('toggled', self.graphZeroToggle_cb)
        bgCheckbutton = prefs_ui.get_object('bgCheckbutton')
        bgCheckbutton.set_active(self.applet.settings["background"])
        bgCheckbutton.connect('toggled', self.bgCheckbutton_cb)
        bgColorbutton = prefs_ui.get_object('bgColorbutton')
        bgColor, bgAlpha = self.applet.settings["background_color"].split("|")
        bgColorbutton.set_color(gtk.gdk.Color(bgColor))
        bgColorbutton.set_alpha(int(float(bgAlpha) * 65535.0))
        bgColorbutton.connect('color-set', self.backgroundColorbutton_color_set_cb)
        borderCheckbutton = prefs_ui.get_object('borderCheckbutton')
        borderCheckbutton.set_active(self.applet.settings["border"])
        borderCheckbutton.connect('toggled', self.borderCheckbutton_cb)
        borderColorbutton = prefs_ui.get_object('borderColorbutton')
        borderColor, borderAlpha = self.applet.settings["border_color"].split("|")
        borderColorbutton.set_color(gtk.gdk.Color(borderColor))
        borderColorbutton.set_alpha(int(float(borderAlpha) * 65535.0))
        borderColorbutton.connect('color-set', self.borderColorbutton_color_set_cb)
        labelNoneRadiobutton = prefs_ui.get_object('labelNoneRadiobutton')
        labelSumRadiobutton = prefs_ui.get_object('labelSumRadiobutton')
        labelBothRadiobutton = prefs_ui.get_object('labelBothRadiobutton')
        if self.parent.label_control == 0:
            labelNoneRadiobutton.set_active(True)
        elif self.parent.label_control == 1:
            labelSumRadiobutton.set_active(True)
        else:
            labelBothRadiobutton.set_active(True)
        labelNoneRadiobutton.connect('toggled', self.labelRadio_cb, 0)
        labelSumRadiobutton.connect('toggled', self.labelRadio_cb, 1)
        labelBothRadiobutton.connect('toggled', self.labelRadio_cb, 2)
        for device in sorted(self.parent.device_usage.interfaces):
            if not "Multi Interface" in device and not "Sum Interface" in device:
                if self.parent.device_usage.interfaces[device]['include_in_sum'] == True:
                    include_in_sum = 1
                else:
                    include_in_sum = 0
                if self.parent.device_usage.interfaces[device]['include_in_multi'] == True:
                    include_in_multi = 1
                else:
                    include_in_multi = 0
                current_iter = store.append([device, include_in_sum, include_in_multi, '', '', '#ff0000', '#ffff00'])
        prefs_ui.get_object("scrolledwindow1").add_with_viewport(cell_box)
        prefs_ui.get_object("dialog-notebook").reparent(preferences_vbox)

    def graphZeroToggle_cb(self, widget):
        self.parent.graph_zero = 0 if widget.get_active() else 1
        self.applet.settings['graph_zero'] = self.parent.graph_zero

    def labelRadio_cb(self, widget, setting):
        if widget.get_active():
            self.applet.settings["label_control"] = setting
            self.parent.label_control = setting

    def create_treeview(self):
        cell_box = gtk.HBox()
        liststore = gtk.ListStore(str, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, str, str)
        treeview = gtk.TreeView(liststore)
        treeview.set_property("rules-hint", True)
        treeview.set_enable_search(True)
        treeview.position = 0
        rows = gtk.VBox(False, 3)
        self.liststore = liststore
        listcols = gtk.HBox(False, 0)
        prows = gtk.VBox(False, 0)
        rows.pack_start(listcols, True, True, 0)
        listcols.pack_start(treeview)
        listcols.pack_start(prows, False, False, 0)
        selection = treeview.get_selection()
        selection.connect('changed', self.on_selection_changed)
        ''' Device '''
        device_renderer = gtk.CellRendererText()
        device_column = gtk.TreeViewColumn("Device", device_renderer)
        device_column.set_property('expand', True)
        device_column.add_attribute(device_renderer, "text", 0)
        ''' Sum '''
        sum_renderer = gtk.CellRendererToggle()
        sum_column = gtk.TreeViewColumn("Sum", sum_renderer)
        sum_column.add_attribute(sum_renderer, 'active', 1)
        sum_renderer.set_property('activatable', True)
        sum_renderer.connect('toggled', self.toggle_cb, liststore, 1, "sum")
        ''' Multi '''
        multi_renderer = gtk.CellRendererToggle()
        multi_column = gtk.TreeViewColumn("Mutli", multi_renderer)
        multi_column.add_attribute(multi_renderer, 'active', 2)
        multi_renderer.set_property('activatable', True)
        multi_renderer.connect('toggled', self.toggle_cb, liststore, 2, "multi")
        ''' Upload '''
        uploadColor_renderer = gtk.CellRendererToggle()
        uploadColor_renderer.set_property('indicator-size', 0.1)
        uploadColor_column = gtk.TreeViewColumn("Upload Color", uploadColor_renderer, cell_background=5)
        uploadColor_column.add_attribute(uploadColor_renderer, 'active', 3)
        uploadColor_column.set_cell_data_func(uploadColor_renderer, self.devlist_cell_func)
        uploadColor_renderer.set_property('activatable', True)
        uploadColor_renderer.connect('toggled', self.color_cb, liststore, 3, "upload")
        ''' Download '''
        downloadColor_renderer = gtk.CellRendererToggle()
        downloadColor_renderer.set_property('indicator-size', 0.1)
        downloadColor_column = gtk.TreeViewColumn("Download Color", downloadColor_renderer, cell_background=6)
        downloadColor_column.add_attribute(downloadColor_renderer, 'active', 4)
        downloadColor_column.set_cell_data_func(downloadColor_renderer, self.devlist_cell_func)
        downloadColor_renderer.set_property('activatable', True)
        downloadColor_renderer.connect('toggled', self.color_cb, liststore, 4, "download")
        ''' Apply the before defined cells '''
        cell_box.liststore = liststore
        treeview.append_column(device_column)
        treeview.append_column(sum_column)
        treeview.append_column(multi_column)
        treeview.append_column(uploadColor_column)
        treeview.append_column(downloadColor_column)
        cell_box.listcols = listcols
        cell_box.add(rows)
        return cell_box

    def on_selection_changed(self, selection):
        ''' If a row is selected; deselect it.. always..
            There is currently no need to have the row selected,
            and the highlight of the row makes it difficult to see
            the colors selected depending on your GTK theme.. '''
        model, paths = selection.get_selected_rows()
        if paths:
            selection.unselect_path(model[paths[0]].path)

    def devlist_cell_func(self, column, cell, model, iter):
        ''' Changes the cell color to match the preferece or selected value '''
        device = self.liststore.get_value(iter, 0)
        column_title = column.get_title().lower().split(" ")[0]
        cell.set_property("cell-background", self.get_color(device, column_title))

    def bgCheckbutton_cb(self, widget):
        self.applet.settings['background'] = widget.get_active()
        self.parent.background = widget.get_active()

    def borderCheckbutton_cb(self, widget):
        self.applet.settings['border'] = widget.get_active()
        self.parent.border = widget.get_active()

    def backgroundColorbutton_color_set_cb(self, widget):
        color = widget.get_color()
        alpha = float("%2.1f" % (widget.get_alpha() / 65535.0))
        self.applet.settings["background_color"] = "%s|%s" % (color, alpha)
        self.parent.background_color = "%s|%s" % (color, alpha)

    def borderColorbutton_color_set_cb(self, widget):
        color = widget.get_color()
        alpha = float("%2.1f" % (widget.get_alpha() / 65535.0))
        self.applet.settings["border_color"] = "%s|%s" % (color, alpha)
        self.parent.border_color = "%s|%s" % (color, alpha)

    def get_color(self, device, column_name):
        if column_name == "upload":
            i = 3
            color = "#ff0000"
        else:
            i = 4
            color = "#ffff00"
        prefs = self.applet.settings["device_display_parameters"]
        for device_pref in prefs:
            device_pref_values = device_pref.split("|")
            if device_pref_values[0] == device:
                if "#" in device_pref_values[i]:
                    color = device_pref_values[i]
        return color

    def color_cb(self, widget, path, model, col_number, name):
        if col_number == 3:
            prop = "Upload"
        else:
            prop = "Download"
        colorseldlg = gtk.ColorSelectionDialog("%s %s Color" % (model[path][0], prop))
        colorseldlg.colorsel.set_current_color(gtk.gdk.Color(self.get_color(model[path][0], prop.lower())))
        response = colorseldlg.run()
        if response == gtk.RESPONSE_OK:
            self.color_choice = colorseldlg.colorsel.get_current_color()
            self.parent.device_usage.interfaces[model[path][0]]['%s_color' % prop.lower()] = self.color_choice.to_string()
            prefs = self.applet.settings["device_display_parameters"]
            if not prefs:
                prefs = ["%s|True|True|None|None" % (model[path][0])]
            if not model[path][0] in prefs.__str__():
                prefs.append("%s|True|True|None|None" % (model[path][0]))
            for i, device_pref in enumerate(prefs):
                dpv = device_pref.split('|')
                if dpv[0] == model[path][0]:
                    ''' If the current column is 1 or 2, it is a checkbox,
                    so transpose from bool to int '''
                    dpv[col_number] = self.color_choice.to_string()
                    prefs[i] = '|'.join(dpv)
            model[path][col_number + 2] = self.color_choice.to_string()
            self.applet.settings["device_display_parameters"] = prefs
        colorseldlg.hide()

    def toggle_cb(self, widget, path, model, col_number, name):
        model[path][col_number] = not model[path][col_number]
        parameter = model[path][col_number]
        self.parent.device_usage.interfaces[model[path][0]]['include_in_%s' % name] = parameter
        prefs = self.applet.settings["device_display_parameters"]
        if not prefs:
            prefs = ["%s|True|True|None|None" % (model[path][0])]
        if not model[path][0] in prefs.__str__():
            prefs.append("%s|True|True|None|None" % (model[path][0]))
        for i, device_pref in enumerate(prefs):
            dpv = device_pref.split('|')
            if dpv[0] == model[path][0]:
                ''' If the current column is 1 or 2, it is a checkbox,
                so transpose from bool to int '''
                dpv[col_number] = parameter
                prefs[i] = '|'.join(dpv)
        self.applet.settings["device_display_parameters"] = prefs
