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
import gnomevfs
import gtk
import pango
import os

class GUITransfer(object):

    def __init__(self, src, dst, options):
        self.__progress = None
        self.cancel = False
        self.txt_operation = ""
        self.label_under = None
        if not (options & gnomevfs.XFER_LINK_ITEMS):
            if (options & gnomevfs.XFER_REMOVESOURCE):
                self.txt_operation = "Moving"
            elif (options & gnomevfs.XFER_EMPTY_DIRECTORIES):
                self.txt_operation = "Deleting"
            else:
                self.txt_operation = "Copying"
            self.dialog = gtk.Dialog(title=self.txt_operation + " files",
                                     buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
            self.dialog.set_border_width(12)
            self.dialog.set_has_separator(False)
            self.dialog.vbox.set_spacing(2)
            hbox_copy = gtk.HBox(False, 0)
            label_copy = gtk.Label("")
            label_copy.set_markup("<big><b>" + self.txt_operation + " files</b></big>\n")
            hbox_copy.pack_start(label_copy, False, False, 0)
            self.dialog.vbox.add(hbox_copy)
            hbox_info = gtk.HBox(False, 0)
            label_fromto = gtk.Label("")
            label_fromto.set_markup("<b>From:</b>\n<b>To:</b>")
            label_fromto.set_justify(gtk.JUSTIFY_RIGHT)
            hbox_info.pack_start(label_fromto, False, False, 0)
            try:
                srcdir = src[0].parent.path
                dstdir = dst[0].parent.path
                label_srcdst = gtk.Label("")
                label_srcdst.set_alignment(0.0, 0.5)
                label_srcdst.set_ellipsize(pango.ELLIPSIZE_START)
                label_srcdst.set_markup("%s\n%s" % (srcdir, dstdir))
                hbox_info.pack_start(label_srcdst, True, True, 4)
            except:
                label_fromto.hide()
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
            self.dialog.set_size_request(400,180)
            self.dialog.connect("response", self._dialog_response)

        self.handle = gnomevfs.async.xfer(
            source_uri_list=src, target_uri_list=dst,
            xfer_options=options,
            error_mode=gnomevfs.XFER_ERROR_MODE_ABORT,
            overwrite_mode=gnomevfs.XFER_OVERWRITE_MODE_ABORT,
            progress_update_callback=self.update_info_cb,
            update_callback_data=options,
            progress_sync_callback=None,
            sync_callback_data=None
            )

        # show dialog after 1 sec
        gobject.timeout_add(1000, self._dialog_show)

    def _dialog_show(self):
        if self.dialog: # and enough data still to be copie?
            self.dialog.show_all()

    def _dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_REJECT or \
           response == gtk.RESPONSE_DELETE_EVENT:
            self.cancel = True


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


class VfsUri(gobject.GObject):

    uri = None

    def __init__(self, uri):
        gobject.GObject.__init__(self)
        if isinstance(uri, gnomevfs.URI):
            self.uri = uri
        else:
            self.uri = gnomevfs.URI(uri.strip())


    def equals(self, uri2):
        return gnomevfs.uris_match(self.as_string(), uri2.as_string())


    def as_uri(self):
        return self.uri


    def as_string(self):
        ustr = self.uri.scheme + "://"
        if self.uri.user_name is not None:
            ustr += self.uri.user_name
            if self.uri.password is not None:
                ustr += ":" + self.uri.password 
            ustr += "@"
        if self.uri.host_name is not None:
            ustr += self.uri.host_name
            if self.uri.host_port > 0:
                ustr += ":" + str(self.uri.host_port)
        if self.uri.path is not None:
            ustr += self.uri.path
        return ustr


class Monitor(gobject.GObject):

    __gsignals__ = {
        "event" :   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                    (gobject.TYPE_STRING, gobject.TYPE_INT)),
        "created" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT,)),
        "deleted" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT,)),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_OBJECT,))
    }

    event_mapping = {
        gnomevfs.MONITOR_EVENT_CREATED : "created",
        gnomevfs.MONITOR_EVENT_DELETED : "deleted",
        gnomevfs.MONITOR_EVENT_CHANGED : "changed",
        gnomevfs.MONITOR_EVENT_METADATA_CHANGED : "changed"
    }

    monitor = None
    vfs_uri = None
    monitor_type = None

    def __init__(self, vfs_uri):
        assert isinstance(vfs_uri, VfsUri)
        gobject.GObject.__init__(self)
        self.vfs_uri = vfs_uri
        type = gnomevfs.get_file_info(vfs_uri.as_uri(),
                gnomevfs.FILE_INFO_DEFAULT | 
                gnomevfs.FILE_INFO_FOLLOW_LINKS).type
        if type == gnomevfs.FILE_TYPE_DIRECTORY:
            self.monitor_type = gnomevfs.MONITOR_DIRECTORY
        elif type == gnomevfs.FILE_TYPE_REGULAR:
            self.monitor_type = gnomevfs.MONITOR_FILE
        else:
            raise gnomevfs.NotSupportedError
        try:
            self.monitor = gnomevfs.monitor_add(
                    vfs_uri.as_string(),
                    self.monitor_type,
                    self._monitor_cb)
        except gnomevfs.NotSupportedError:
            return None


    def _monitor_cb(self, monitor_uri, info_uri, event):
        signal = self.event_mapping[event]
        if signal:
            if self.monitor_type == gnomevfs.MONITOR_FILE:
                self.emit(signal, self.vfs_uri)
            else:
                self.emit(signal, VfsUri(info_uri))


    def close(self):
        try: 
            gnomevfs.monitor_cancel(self.monitor)
            self.monitor = None
        except:
            return
