import gobject
import gtk
import gtk.glade

class GladeWindow(gobject.GObject):
    """
    Base class for dialogs or windows backed by glade interface definitions.
 
    Example:
    class MyWindow(GladeWindow):
        glade_file = 'my_glade_file.glade'
        ...

    Remember to chain up if you customize __init__(). Also note that GladeWindow
    does *not* descend from GtkWindow, so you can't treat the resulting object
    as a GtkWindow. The show, hide, destroy, and present methods are provided as
    convenience wrappers.
    """

    glade_file = None
    window = None

    def __init__(self, parent=None):
        gobject.GObject.__init__(self)
        wtree = gtk.glade.XML(self.glade_file)
        self.widgets = {}
        for widget in wtree.get_widget_prefix(''):
            wname = widget.get_name()
            if isinstance(widget, gtk.Window):
                    assert self.window == None
                    self.window = widget
                    continue
               
            if wname in self.widgets:
                raise AssertionError("Two objects with same name (%s): %r %r"
                                     % (wname, self.widgets[wname], widget))
            self.widgets[wname] = widget
   
        if parent is not None: 
            self.window.set_transient_for(parent)
  
        wtree.signal_autoconnect(self)
   
        self.destroy = self.window.destroy
        self.show = self.window.show
        self.hide = self.window.hide
        self.present = self.window.present

gobject.type_register(GladeWindow)
