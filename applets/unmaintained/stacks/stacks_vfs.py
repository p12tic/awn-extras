#!/usr/bin/env python

# Copyright (c) 2007 Timon ter Braak
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

import gobject
import gio
import gtk
import pango
import os
from awn.extras import _

class GUITransfer(object):

    dialog = None

    def __init__(self, src, dst, actions):
        self.__progress = None
        self.cancel = False
        self.txt_operation = _("Copying files")
        self.label_under = None
        self.num_items = 1

        # force copying of non-local objects
        if (actions & gtk.gdk.ACTION_LINK):
            if src[0].get_path() is None:
                actions = gtk.gdk.ACTION_COPY

        if not (actions & gtk.gdk.ACTION_LINK):
            if (actions & gtk.gdk.ACTION_MOVE):
                self.txt_operation = _("Moving files")
            elif (actions == 0):
                self.txt_operation = _("Deleting files")
            self.dialog = gtk.Dialog(title=self.txt_operation,
                                     buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
            self.dialog.set_border_width(12)
            self.dialog.set_has_separator(False)
            self.dialog.vbox.set_spacing(2)
            hbox_copy = gtk.HBox(False, 0)
            label_copy = gtk.Label("")
            label_copy.set_markup("<big><b>%s</b></big>\n" % self.txt_operation)
            hbox_copy.pack_start(label_copy, False, False, 0)
            self.dialog.vbox.add(hbox_copy)
            hbox_info = gtk.HBox(False, 0)
            label_fromto = gtk.Label("")
            label_fromto.set_justify(gtk.JUSTIFY_RIGHT)
            hbox_info.pack_start(label_fromto, False, False, 0)
            srcdir = src[0].get_parent().get_uri()
            if len(dst) > 0:
                label_fromto.set_markup("<b>From:</b>\n<b>To:</b>")
                dstdir = dst[0].get_parent().get_uri()
            else:
                dstdir = ""
                label_fromto.set_markup("<b>From:</b>\n")
            label_srcdst = gtk.Label("")
            label_srcdst.set_alignment(0.0, 0.5)
            label_srcdst.set_ellipsize(pango.ELLIPSIZE_START)
            label_srcdst.set_markup("%s\n%s" % (srcdir, dstdir))
            hbox_info.pack_start(label_srcdst, True, True, 4)
            self.dialog.vbox.add(hbox_info)
            self.progress_bar = gtk.ProgressBar()
            self.dialog.vbox.add(self.progress_bar)
            hbox_under = gtk.HBox(False, 0)
            self.label_under = gtk.Label("")
            self.label_under.set_justify(gtk.JUSTIFY_LEFT)
            self.label_under.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
            self.label_under.xalign = 0.0
            hbox_under.pack_start(self.label_under, True, True, 0)
            self.dialog.vbox.add(hbox_under)

            self.status_label = gtk.Label()
            self.dialog.vbox.add(self.status_label)
            self.dialog.set_size_request(400,-1)
            self.dialog.connect("response", self._dialog_response)

        self.cancellable = gio.Cancellable()

        def _copy_callback(file, result, items):
            try:
                if file is None or file.copy_finish(result):
                    if len(items) > 0:
                        source, dest = items.pop()
                        self.label_under.set_markup(
                            "<i>%s %s</i>" % (self.txt_operation, str(source.get_basename())))
                        self.progress_bar.set_text(self.txt_operation + " " +
                            _("%d of %d") % (self.num_items - len(items), self.num_items))
                        source.copy_async(dest, _copy_callback, _copy_progress,
                            cancellable=self.cancellable, user_data=items)
                    else:
                        self._finish()
                else:
                    print "copy failed"
            except gio.Error:
                self._finish()

        def _copy_progress(current, total):
            if self.dialog:
                if current > 0 and total > 0:
                   fraction = float(current)/total
                   self.progress_bar.set_fraction(fraction)

        if actions == 0:
            # remove the whole directory
            print "TODO: We should delete %s" % src

        elif (actions & gtk.gdk.ACTION_MOVE):
            # why the hell isn't there gio.File.move_async() ??
            for item in zip(src, dst):
                source, dest = item
                source.move(dest, cancellable=self.cancellable)
            self._finish()

        elif (actions & gtk.gdk.ACTION_LINK):
            for item in zip(src, dst):
                source, dest = item
                dest.make_symbolic_link(source.get_path())
            self._finish()

        else: # gtk.gdk.ACTION_COPY
            items = zip(src, dst)
            items.reverse()
            self.num_items = len(items)
            _copy_callback(None, None, items)

        # show dialog after 1 sec
        gobject.timeout_add(1000, self._dialog_show)

    def _finish(self):
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None

    def _dialog_show(self):
        if self.dialog: # and enough data still to be copied?
            self.dialog.show_all()
        return False


    def _dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_REJECT or \
           response == gtk.RESPONSE_DELETE_EVENT:
            self.cancellable.cancel()

    '''
    def update_info_cb(self, _reserved, info, data):
        if info.status == gnomevfs.XFER_PROGRESS_STATUS_VFSERROR:
            uri = gnomevfs.URI(info.source_name)

            if xfer_opts & gnomevfs.XFER_REMOVESOURCE:
                msg = _("Error while moving.")
                msg2 = _('Cannot move "%s" to the trash because you do not have permissions to change it or its parent folder.' % uri.short_name)
            elif xfer_opts & gnomevfs.XFER_DELETE_ITEMS:
                msg = _("Error while deleting.")
                msg2 = _('"%s" cannot be deleted because you do not have permissions to modify its parent folder.') % uri.short_name
            else:
                msg = _("Error while performing file operation.")
                msg2 = _('Cannot perform file operation %d on "%s".')  % (xfer_opts, uri.short_name)
            dialog = gtk.MessageDialog(type = gtk.MESSAGE_ERROR,
                    message_format = msg)
            dialog.format_secondary_text(msg2)
            if info.files_total > 1:
                button = gtk.Button(label=_("_Skip"))
                button.show()
                dialog.add_action_widget(button, gtk.RESPONSE_REJECT)

            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            button = gtk.Button(label=_("_Retry"))
            button.set_property("can-default", True)
            button.show()
            dialog.add_action_widget(button, gtk.RESPONSE_ACCEPT)
            dialog.set_default_response(gtk.RESPONSE_ACCEPT)

            response = dialog.run()
            dialog.destroy()

            if response == gtk.RESPONSE_ACCEPT:
                return gnomevfs.XFER_ERROR_ACTION_RETRY
            elif response == gtk.RESPONSE_REJECT:
                return gnomevfs.XFER_ERROR_ACTION_SKIP

            return gnomevfs.XFER_ERROR_ACTION_ABORT

        if (data & gnomevfs.XFER_LINK_ITEMS):
            return 1
        if info.phase == gnomevfs.XFER_PHASE_COMPLETED:
            self.dialog.destroy()
        if info.status == gnomevfs.XFER_PROGRESS_STATUS_OK:
            self.label_under.set_markup(
                    "<i>%s %s</i>" % (self.txt_operation, str(info.source_name)))
            self.progress_bar.set_text(self.txt_operation + " " +
                    str(info.file_index) + " of " + str(info.files_total))
            if info.bytes_copied > 0 and info.bytes_total > 0:
                fraction = float(info.bytes_copied)/float(info.bytes_total)
                self.progress_bar.set_fraction(fraction)
        if self.cancel:
            # TODO: remove partial target?
            return 0
        return 1
    '''


class VfsUri(gobject.GObject):

    uri = None

    def __init__(self, uri):
        gobject.GObject.__init__(self)
        if isinstance(uri, gio.File):
            self.uri = uri
        else:
            self.uri = gio.File(uri.strip())

    def create_child(self, short_name):
        if isinstance(short_name, gio.File):
            short_name = short_name.get_basename()
        return self.uri.get_child_for_display_name(short_name)


    def equals(self, uri2):
        return self.uri.equal(uri2.as_uri())


    def as_uri(self):
        return self.uri


    def as_string(self):
        return self.uri.get_uri()


class Monitor(gobject.GObject):

    __gsignals__ = {
        "event" :   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                    (gobject.TYPE_STRING, gobject.TYPE_INT)),
        "created" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT,)),
        "deleted" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT,)),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT,))
    }

    event_mapping = {
        gio.FILE_MONITOR_EVENT_CREATED : "created",
        gio.FILE_MONITOR_EVENT_DELETED : "deleted",
        gio.FILE_MONITOR_EVENT_CHANGED : "changed",
        gio.FILE_MONITOR_EVENT_CHANGES_DONE_HINT: "changed",
        gio.FILE_MONITOR_EVENT_ATTRIBUTE_CHANGED : "changed"
    }

    monitor = None
    vfs_uri = None
    monitor_type = None

    def __init__(self, vfs_uri):
        assert isinstance(vfs_uri, VfsUri)
        gobject.GObject.__init__(self)
        self.vfs_uri = vfs_uri

        # FIXME: this might be unnecessary
        self.type = vfs_uri.as_uri().query_file_type(0, gio.Cancellable())
        '''
        if type == gio.FILE_TYPE_DIRECTORY:
            self.monitor_type = gnomevfs.MONITOR_DIRECTORY
        elif type == gio.FILE_TYPE_REGULAR:
            self.monitor_type = gnomevfs.MONITOR_FILE
        else:
            raise RuntimeError("Not Supported")
        '''
        try:
            self.monitor = self.vfs_uri.as_uri().monitor()
            self.monitor.connect("changed", self._monitor_cb)
        except Exception:
            return None


    def _monitor_cb(self, monitor, monitor_uri, other_uri, event):
        signal = None
        try:
            signal = self.event_mapping[event]
        except:
            return

        if self.type == gio.FILE_TYPE_DIRECTORY:
            self.emit(signal, VfsUri(monitor_uri))
        else:
            self.emit(signal, self.vfs_uri)


    def close(self):
        try: 
            self.monitor.cancel()
            self.monitor = None
            self.vfs_uri = None
        except:
            return
