#! /usr/bin/env python
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
        if not (options & gnomevfs.XFER_LINK_ITEMS):
            if (options & gnomevfs.XFER_REMOVESOURCE):
                self.txt_operation = "Moving"
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
            label_srcdst = gtk.Label("")
            label_srcdst.set_alignment(0.0, 0.5)
            label_srcdst.set_markup("%s\n%s" %
                    (str(src.dirname), str(dst.dirname)))
            label_srcdst.set_ellipsize(pango.ELLIPSIZE_START)
            hbox_info.pack_start(label_srcdst, True, True, 4)
            self.dialog.vbox.add(hbox_info)
            self.progress_bar = gtk.ProgressBar()
            self.dialog.vbox.add(self.progress_bar)
            hbox_under = gtk.HBox(False, 0)
            self.label_under = gtk.Label("")
            self.label_under.set_justify(gtk.JUSTIFY_LEFT)
            self.label_under.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
            hbox_under.pack_start(self.label_under, True, True, 0)
            self.dialog.vbox.add(hbox_under)

            self.status_label = gtk.Label()
            self.dialog.vbox.add(self.status_label)        
            self.dialog.set_size_request(400,180)
            self.dialog.connect("response", self.__dialog_response)
            self.dialog.show_all()

        self.handle = gnomevfs.async.xfer(
            source_uri_list=[src], target_uri_list=[dst],
            xfer_options=options,
            error_mode=gnomevfs.XFER_ERROR_MODE_ABORT,
            overwrite_mode=gnomevfs.XFER_OVERWRITE_MODE_ABORT,
            progress_update_callback=self.update_info_cb,
            update_callback_data=options,
            progress_sync_callback=None,
            sync_callback_data=None
            )       
            
    def __dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_REJECT or \
           response == gtk.RESPONSE_DELETE_EVENT:
            self.cancel = True

    def update_info_cb(self, _reserved, info, data):
        if (data & gnomevfs.XFER_LINK_ITEMS):
            return 1
        if info.phase == gnomevfs.XFER_PHASE_COMPLETED:
            self.dialog.destroy()
        if info.status == gnomevfs.XFER_PROGRESS_STATUS_OK:
            self.label_under.set_markup(
                    "<i>%s %s</i>" % (self.txt_operation, str(info.source_name)))
            self.progress_bar.set_text("Copying file: " + 
                    str(info.file_index) + " of " + str(info.files_total))
            if info.bytes_copied > 0 and info.bytes_total > 0:
                self.progress_bar.set_fraction(float(info.bytes_copied)/float(info.bytes_total))
        if self.cancel:
            return 0
        return 1



FILE = gnomevfs.FILE_TYPE_REGULAR
DIR = gnomevfs.FILE_TYPE_DIRECTORY
LINK = gnomevfs.FILE_TYPE_SYMBOLIC_LINK

def get_vfsuri(uri):
    try:
        return VfsFile(uri)
    except:
        try:
            return VfsDir(uri)
        except:
            return VfsUri(uri, False)
    raise gnomevfs.NotSupportedError 

class VfsCache:

    cache = {}

    @staticmethod
    def load(uri):
        if VfsCache.cache.has_key(uri):
            return VfsCache.cache[uri]
        else:   return None

    @staticmethod
    def store(uri,handle):
        VfsCache.cache[uri] = handle

class VfsUri(gobject.GObject):

    __gsignals__ = {
        "event" :   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                    (gobject.TYPE_STRING, gobject.TYPE_INT)),
        "created" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        "deleted" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
    }

    event_mapping = {
        gnomevfs.MONITOR_EVENT_CREATED : "created",
        gnomevfs.MONITOR_EVENT_DELETED : "deleted",
        gnomevfs.MONITOR_EVENT_CHANGED : "changed",
        gnomevfs.MONITOR_EVENT_METADATA_CHANGED : "changed"
    }

    vfs_uri = None
    short_name = None
    handle = None
    file_info = None
    monitor = None
    pending_timeouts = {}

    def __init__(self, uri, create):
        gobject.GObject.__init__(self)
        if isinstance(uri, gnomevfs.URI):
            self.vfs_uri = uri
        else:
            self.vfs_uri = gnomevfs.URI(self._vfs_clean_uri(uri))
        self.short_name = self.vfs_uri.short_name

        if isinstance(self, VfsDir):
            if str(self.vfs_uri)[-1] != '/':
                self.vfs_uri = self.vfs_uri.append_string("/")

        if not gnomevfs.exists(self.vfs_uri) and create:
            print "uri does not exist, creating: ", self.vfs_uri
            self._create()


    def _vfs_clean_uri(self, uri):
        """return an uri from an uri or a local path"""
        try:
            gnomevfs.URI(uri)
            gnomevfs.Handle(uri)
        except : #gnomevfs.InvalidURIError:
            # maybe a local path ?
            local = os.path.abspath(uri)
            if os.path.exists(local):
                uri = gnomevfs.get_uri_from_local_path(local)
            #uri = gnomevfs.escape_host_and_path_string(uri)
        return uri

    def equals(self, uri):
        return gnomevfs.uris_match(self.to_string(), uri.to_string())        

    def to_string(self):
        ustr = self.vfs_uri.scheme + "://"
        if self.vfs_uri.user_name is not None:
            ustr += self.vfs_uri.user_name
            if self.vfs_uri.password is not None:
                ustr += ":" + self.vfs_uri.password 
            ustr += "@"
        if self.vfs_uri.host_name is not None:
            ustr += self.vfs_uri.host_name
            if self.vfs_uri.host_port > 0:
                ustr += ":" + str(self.vfs_uri.host_port)
        if self.vfs_uri.path is not None:
            ustr += self.vfs_uri.path
        return ustr #gnomevfs.unescape_string(ustr, "")

#    def unescape_string(self):
#        return gnomevfs.unescape_string_for_display(self.vfs_uri)

    def get_type(self):
        if self.file_info is None:
            try:
                self.file_info = gnomevfs.get_file_info(self.vfs_uri, 
                    gnomevfs.FILE_INFO_GET_MIME_TYPE | gnomevfs.FILE_INFO_FOLLOW_LINKS)
            except gnomevfs.Error:
                return None
        return self.file_info.type

    def _create(self):
        raise gnomevfs.NotSupportedError

    def _open(self):
        raise gnomevfs.NotSupportedError

    def close(self):
        if self.monitor is not None:
            gnomevfs.monitor_cancel(self.monitor)
            self.monitor = None

    def read(self):
        raise gnomevfs.NotSupportedError

    def write(self):
        raise gnomevfs.NotSupportedError

    def append(self):
        raise gnomevfs.NotSupportedError

    def monitor(self):
        if self.get_type() == DIR:
            monitor_type = gnomevfs.MONITOR_DIRECTORY
        elif self.get_type() == FILE:
            monitor_type = gnomevfs.MONITOR_FILE
        else:
            raise gnomevfs.NotSupportedError
        try:
            self.monitor = gnomevfs.monitor_add(self.to_string(), 
                                            monitor_type, 
                                            self._monitor_cb)
        except gnomevfs.NotSupportedError:
            # could be a non local file
            return

    def _monitor_cb(self, monitor_uri, info_uri, event):
        signal = self.event_mapping[event]
        if signal:
            self.emit(signal, info_uri)

#   def remove(self):
#       raise gnomevfs.NotSupportedError

#   def move(self):
#       raise gnomevfs.NotSupportedError

#   def copy(self):
#       raise gnomevfs.NotSupportedError

#   def link(self):
#       raise gnomevfs.NotSupportedError           

class VfsFile(VfsUri):

    def __init__(self, uri, create=False):
        VfsUri.__init__(self, uri, create)
        assert self.get_type() is FILE

    def _create(self):
        gnomevfs.create(self.vfs_uri, gnomevfs.OPEN_WRITE) 

    def _open(self):
        cached = VfsCache.load(self.vfs_uri)
        if cached is not None:
            self.handle = cached
        else:    
            mode = gnomevfs.OPEN_WRITE
            try:
                self.handle = gnomevfs.open(self.vfs_uri, mode)
                VfsCache.store(self.vfs_uri, self.handle)
            except:
                self.handle = None

    def close(self):
        if self.handle is not None:
            self.handle.close()
        VfsUri.close(self)

    def read(self):
        return gnomevfs.read_entire_file(self.to_string())

    def write(self, buffer):
        if self.handle is None:
            self._open()        
        if buffer is None:
            gnomevfs.truncate(self.vfs_uri, 0)
        else:
            self.handle.write(buffer)

    def append(self, buffer):
        seek_to_end = self.read()
        self.write(buffer)

class VfsDir(VfsUri):

    def __init__(self, uri, create=False):
        VfsUri.__init__(self, uri, create)
        assert self.get_type() is DIR

    def _create(self):
        path = self.vfs_uri.path
        self.vfs_uri = self.vfs_uri.resolve_relative("/")
        for folder in path.split("/"):
            if not folder:
                continue
            self.vfs_uri = self.vfs_uri.append_string(folder)
            try:
                gnomevfs.make_directory(self.vfs_uri, 0777)
            except gnomevfs.FileExistsError:
                pass
            except:
                return False
        return True 

    def _open(self):
        self.handle = gnomevfs.open_directory(self.vfs_uri)
    
    def read(self):
        if self.handle is None:
            self._open()
        filelist = []   
        for file_info in self.handle:
            if file_info.name[0] == "." or file_info.name.endswith("~"):
                continue
            if file_info.type == FILE or \
                    file_info.type == DIR or \
                    file_info.type == LINK:
                filelist.append( str(self.vfs_uri.append_file_name(file_info.name)) )
        return filelist

