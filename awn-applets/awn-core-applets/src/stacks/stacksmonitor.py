import gobject
import os
import gnomevfs

class FileMonitor(gobject.GObject):
    '''
    A simple wrapper around Gnome VFS file monitors.  Emits created, deleted,
    and changed events.  Incoming events are queued, with the latest event
    cancelling prior undelivered events.
    '''
    
    __gsignals__ = {
        "event" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                   (gobject.TYPE_STRING, gobject.TYPE_INT)),
        "created" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        "deleted" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
    }

    def __init__(self, path):
        gobject.GObject.__init__(self)
        self.path = path.scheme + "://" + path.path
        try:
            self.type = gnomevfs.get_file_info(path).type
        except gnomevfs.Error:
            self.type = gnomevfs.MONITOR_FILE

        self.monitor = None
        self.pending_timeouts = {}

    def open(self):
        if not self.monitor:
            if self.type == gnomevfs.FILE_TYPE_DIRECTORY:
                monitor_type = gnomevfs.MONITOR_DIRECTORY
            else:
                monitor_type = gnomevfs.MONITOR_FILE
            self.monitor = gnomevfs.monitor_add(self.path, monitor_type, self._queue_event)

    def _clear_timeout(self, info_uri):
        try:
            gobject.source_remove(self.pending_timeouts[info_uri])
            del self.pending_timeouts[info_uri]
        except KeyError:
            pass

    def _queue_event(self, monitor_uri, info_uri, event):
        self._clear_timeout(info_uri)
        self.pending_timeouts[info_uri] = \
            gobject.timeout_add(250, self._timeout_cb, monitor_uri, info_uri, event)

    def queue_changed(self, info_uri):
        self._queue_event(self.path, info_uri, gnomevfs.MONITOR_EVENT_CHANGED)

    def close(self):
        gnomevfs.monitor_cancel(self.monitor)
        self.monitor = None

    def _timeout_cb(self, monitor_uri, info_uri, event):
        if event in (gnomevfs.MONITOR_EVENT_METADATA_CHANGED,
                     gnomevfs.MONITOR_EVENT_CHANGED):
            self.emit("changed", info_uri)
        elif event == gnomevfs.MONITOR_EVENT_CREATED:
            self.emit("created", info_uri)
        elif event == gnomevfs.MONITOR_EVENT_DELETED:
            self.emit("deleted", info_uri)
        self.emit("event", info_uri, event)

        self._clear_timeout(info_uri)
        return False
