# Copyright (c) 2008  onox <denkpadje@gmail.com>
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

try:
    import glib
except ImportError:
    import gobject as glib

from awn import check_dependencies
check_dependencies(globals(), "pynotify")

# Minutes until the a closed warning is shown again
warning_closed_timeout = 5.0


class MessageHandler:

    def __init__(self, applet):
        self.applet = applet

        pynotify.init(applet.applet.meta["short"])
        self.message = pynotify.Notification("Battery") # dummy value (will be replaced later)

        self.set_next(InvisibleMessageState)

    def set_next(self, state):
        self.__state = state(self)

    def evaluate(self):
        self.__state.evaluate()


class InvisibleMessageState:

    def __init__(self, handler):
        self.handler = handler

        try:
            self.handler.message.close()
        except glib.GError:
            pass # Ignore error thrown when there's no message to close

    def evaluate(self):
        if self.handler.applet.settings["warn-low-level"]:
            warn = self.handler.applet.is_battery_low()
            if warn is not None and warn:
                self.handler.set_next(VisibleWarningState)
        if self.handler.applet.settings["notify-high-level"] and self.handler.applet.is_battery_high():
            self.handler.set_next(VisibleNotificationState)


class VisibleWarningState:

    __closed = False

    def __init__(self, handler):
        self.handler = handler

        self.handler.message.set_property("summary", "Battery is running low")
        self.handler.message.set_property("icon-name", "dialog-warning")
        self.handler.message.set_urgency(pynotify.URGENCY_NORMAL)
        self.__closed_id = self.handler.message.connect("closed", self.__closed_cb)
        self.update_message()

    def __stop(self):
        self.handler.message.disconnect(self.__closed_id)

    def evaluate(self):
        if self.handler.applet.settings["warn-low-level"]:
            warn = self.handler.applet.is_battery_low()
            if warn is None or warn:
                if self.handler.applet.backend.is_below_low_capacity():
                    self.__stop()
                    self.handler.set_next(VisibleErrorState)
                if not self.__closed:
                    self.update_message()
                return
        self.__stop()
        self.handler.set_next(InvisibleMessageState)

    def update_message(self):
        backend = self.handler.applet.backend
        time = backend.get_remaining_time()
        if time is not None:
            body = "You have approximately <b>%s</b> of remaining battery power (%d%%)." % (self.handler.applet.format_time(time), backend.get_capacity_percentage())
            self.handler.message.set_property("body", body)
            self.handler.message.set_timeout(time[0] * 60 * 60000 + time[1] * 60000)
            self.handler.message.show()

    def __closed_cb(self, message):
        self.__closed = True

        if self.handler.applet.backend.get_remaining_time()[1] >= 10:
            seconds = warning_closed_timeout * 60
        else:
            seconds = 60

        """May be fired even after the state switches to a different object, but
        it doesn't do any harm because this object (self) is not used then anymore"""
        def set_closed():
            self.__closed = False
        self.handler.applet.applet.timing.delay(set_closed, seconds)


class VisibleErrorState(VisibleWarningState):

    def __init__(self, handler):
        self.handler = handler

        # Close to avoid messing up the message when the urgency changes
        self.handler.message.close()

        self.handler.message.set_property("summary", "Battery is critically low")
        self.handler.message.set_property("icon-name", "dialog-warning")
        self.handler.message.set_urgency(pynotify.URGENCY_CRITICAL)
        self.update_message()

    def evaluate(self):
        if self.handler.applet.settings["warn-low-level"]:
            warn = self.handler.applet.is_battery_low()
            if warn is None or warn:
                self.update_message()
                return
        self.handler.set_next(InvisibleMessageState)


class VisibleNotificationState:

    __closed = False

    def __init__(self, handler):
        self.handler = handler

        self.handler.message.set_property("summary", "Battery is charged")
        self.handler.message.set_property("icon-name", "dialog-information")
        self.handler.message.set_timeout(0)
        self.handler.message.set_urgency(pynotify.URGENCY_NORMAL)
        self.__closed_id = self.handler.message.connect("closed", self.__closed_cb)
        self.__update_message()

    def __stop(self):
        self.handler.message.disconnect(self.__closed_id)

    def evaluate(self):
        if self.handler.applet.settings["notify-high-level"] and self.handler.applet.is_battery_high():
            if not self.__closed:
                self.__update_message()
            return
        self.__stop()
        self.handler.set_next(InvisibleMessageState)

    def __update_message(self):
        charge_percentage = self.handler.applet.backend.get_capacity_percentage()
        if charge_percentage == 100:
            body = "Your battery is fully charged."
        else:
            body = "Your battery is charged to <b>%d%%</b>." % charge_percentage
        self.handler.message.set_property("body", body)
        self.handler.message.show()

    def __closed_cb(self, message):
        self.__closed = True
