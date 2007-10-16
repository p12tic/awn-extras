#! /usr/bin/env python
import gnomevfs
import gtk
import pango
import gobject

class GUITransfer(object):
    def __init__(self, src, dst, options):
        self.__progress = None
        self.cancel = False
        self.dialog = gtk.Dialog(title="Copying files",
                                 buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        self.dialog.set_border_width(12)
        self.dialog.set_has_separator(False)
        self.dialog.vbox.set_spacing(2)
        hbox_copy = gtk.HBox(False, 0)
        label_copy = gtk.Label("")
        label_copy.set_markup("<big><b>Copying files</b></big>\n")
        hbox_copy.pack_start(label_copy, False, False, 0)
        self.dialog.vbox.add(hbox_copy)
        hbox_info = gtk.HBox(False, 0)
        label_fromto = gtk.Label("")
        label_fromto.set_markup("<b>From:</b>\n<b>To:</b>")
        label_fromto.set_justify(gtk.JUSTIFY_RIGHT)
        hbox_info.pack_start(label_fromto, False, False, 0)
        label_srcdst = gtk.Label("")
        label_srcdst.set_justify(gtk.JUSTIFY_LEFT)
        label_srcdst.set_markup("%s\n%s" %
                (str(src.dirname), str(dst.dirname)))
        label_srcdst.set_ellipsize(pango.ELLIPSIZE_START)
        hbox_info.pack_start(label_srcdst, True, True, 4)
        self.dialog.vbox.add(hbox_info)
        self.progress_bar = gtk.ProgressBar()
        self.dialog.vbox.add(self.progress_bar)
        hbox_under = gtk.HBox(False, 0)
        self.label_under = gtk.Label("")
        self.label_under.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        hbox_under.pack_start(self.label_under, True, True, 0)
        self.dialog.vbox.add(hbox_under)

        self.status_label = gtk.Label()
        self.dialog.vbox.add(self.status_label)        
        self.dialog.set_size_request(400,180)
        self.dialog.show_all()

        self.handle = gnomevfs.async.xfer(
            source_uri_list=[src], target_uri_list=[dst],
            xfer_options=options,
            error_mode=gnomevfs.XFER_ERROR_MODE_ABORT,
            overwrite_mode=gnomevfs.XFER_OVERWRITE_MODE_ABORT,
            progress_update_callback=self.update_info_cb,
            update_callback_data=None,
            progress_sync_callback=None,
            sync_callback_data=None
            )
        
        self.dialog.connect("response", self.__dialog_response)
    
    def __dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_REJECT or \
           response == gtk.RESPONSE_DELETE_EVENT:
            self.cancel = True

    def update_info_cb(self, _reserved, info, data):
        if info.phase == gnomevfs.XFER_PHASE_COMPLETED:
            self.dialog.destroy()
            gtk.main_quit()
        if info.status == gnomevfs.XFER_PROGRESS_STATUS_OK:
            self.label_under.set_markup("<i>Copying %s</i>" % (str(info.source_name)))
            self.progress_bar.set_text("Copying file: " + 
                    str(info.file_index) + " of " + str(info.files_total))
            if info.bytes_copied > 0 and info.bytes_total > 0:
                self.progress_bar.set_fraction(float(info.bytes_copied)/float(info.bytes_total))
        if self.cancel:
            return 0
        return 1
