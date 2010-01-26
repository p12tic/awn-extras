#!/usr/bin/python
#
# Copyright (c) 2009 Michal Hruby <michal.mhr at gmail.com>
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

import sys
import awn
import gtk

if __name__ == "__main__":
    awn.init(sys.argv[1:])
    applet = awn.AppletSimple("python-test", awn.uid, awn.panel_id)
    applet.set_icon_name("gtk-yes") # applet icon
    applet.set_tooltip_text("Test python applet") # will be displayed on hover

    awn.embed_applet(applet)
    gtk.main()
