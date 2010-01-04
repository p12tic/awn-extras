# -*- coding: utf-8 -*-

# Copyright (c) 2008 Moses Palmér
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


import cairo
import gobject
import gtk

from math import cos, ceil, pi, sin


class Scalable:
    """An abstract scalable widget."""
    scale = 1.0
    rsize = (0, 0)
    position = (0, 0)

    def set_scale(self, new_scale):
        """Rescale the widget."""
        old_scale = self.scale
        self.scale = new_scale
        self.do_resize(self.rsize[0] * self.scale, self.rsize[1] * self.scale)
        self.do_scale(old_scale)

    def set_size(self, new_size):
        """Rescale the widget."""
        self.rsize = new_size
        self.do_resize(self.rsize[0] * self.scale, self.rsize[1] * self.scale)

    def do_resize(self, new_width, new_height):
        """Actually do the resizing."""
        pass

    def do_scale(self, old_scale):
        """Actually do the rescaling."""
        pass


def make_int(d):
    """Return an int with adjusted value."""
    return int(ceil(d))


def set_background(widget, pixmap):
    """Sets the background of the widget to that of its parent."""
    if widget.window:
        if pixmap:
            widget.window.set_back_pixmap(pixmap, False)
        else:
            widget.window.set_back_pixmap(None, True)


def update_background(widget, pixmap=None):
    """Set the back pixmap of a parent widget and clear the back pixmap of its
    children."""
    if widget.window:

        def update_background_callback(child):
            """Clear the back pixmap of a child widget."""
            # Only set the back pixmap of widget with a separate gtk.gdk.Window
            if child.window and child.window != widget.window:
                set_background(child, None)

            if isinstance(child, gtk.Container):
                child.forall(update_background_callback)

        set_background(widget, pixmap)
        widget.forall(update_background_callback)


def update_scale(widget):
    """Set the scale of all child widgets."""
    if widget.window:

        def update_scale_callback(child):
            """Change the scale of a child widget."""
            if isinstance(child, Scalable):
                child.set_scale(widget.scale)
                if isinstance(widget, ScalableWidgetContainer):
                    widget.move_scaled(child, *child.position)

            if isinstance(child, gtk.Container):
                update_scale(child)

        widget.foreach(update_scale_callback)


def cairo_clear(ctx):
    """Clear a Cairo context."""
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.restore()


class ScalableWidgetContainer(gtk.Fixed, Scalable):
    """A container for scalable widgets."""
    shape = None

    def do_resize(self, new_width, new_height):
        """Resize the container."""
        self.set_size_request(make_int(new_width), make_int(new_height))

    def do_scale(self, oldscale):
        """Rescale this widget and all its children."""
        update_scale(self)

    def put_scaled(self, widget, x, y):
        """Put a widget in this container."""
        self.put(widget, int(x * self.scale), int(y * self.scale))

        # Set the Scalable attributes
        widget.set_scale(self.scale)
        widget.set_size(map(lambda x: x / widget.scale, widget.size_request()))
        widget.position = (x, y)

    def move_scaled(self, widget, x, y):
        """Move a widget to scaled co-ordinates."""
        self.move(widget, int(x * self.scale), int(y * self.scale))
        widget.position = (x, y)


class ScalableWindow(gtk.Window, Scalable):
    """A scalable top-level window."""
    SHADOW_BLUR_RADIUS = 5
    SHADOW_BLUR_QUALITY = 15

    background = None
    has_shadow = False

    layout = None
    shadow_offset = (1, 1)
    shadow_color = (0.0, 0.0, 0.0, 0.5)
    canvas_size = (0, 0)

    def get_window_offset(self):
        """Return the offset of the window image relative to the top left
        corner."""
        if self.is_composited() and self.has_shadow:
            dx = self.SHADOW_BLUR_RADIUS - self.shadow_offset[0]
            dy = self.SHADOW_BLUR_RADIUS - self.shadow_offset[1]
            if dx < 0:
                dx = 0
            if dy < 0:
                dy = 0
        else:
            dx, dy = (0, 0)

        return (dx, dy)

    def get_shadow_offset(self):
        """Return the offset of the shadow."""
        if self.is_composited() and self.has_shadow:
            dx, dy = self.get_window_offset()
            return (dx + self.shadow_offset[0], dy + self.shadow_offset[1])
        else:
            return (0, 0)

    def get_required_size(self, width, height):
        """Return the actual window size required for a window image of the
        specified size."""
        w, h = width, height
        if self.is_composited() and self.has_shadow:
            w += self.SHADOW_BLUR_RADIUS * 2
            h += self.SHADOW_BLUR_RADIUS * 2
            dx, dy = self.shadow_offset
            if dx > self.SHADOW_BLUR_RADIUS:
                w += dx - self.SHADOW_BLUR_RADIUS
            if dy > self.SHADOW_BLUR_RADIUS:
                h += dy - self.SHADOW_BLUR_RADIUS

        return (w, h)

    def reposition_child(self, child):
        """Update the position of a child widget."""
        self.move_child(child, *child.canvas_position)

    def update_shadow_offset(self):
        """Change size and reposition children when shadow_offset has
        changed."""
        self.canvas_size = self.canvas_size
        self.layout.foreach(self.reposition_child)

    def __init__(self):
        super(ScalableWindow, self).__init__()

        self.set_app_paintable(True)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_events(gtk.gdk.ALL_EVENTS_MASK)

        # Connect signals
        self.connect('map-event', self.__on_map)
        self.connect('size-allocate', self.__on_size_allocate)
        self.connect('screen-changed', self.__on_screen_changed)
        self.connect('button-press-event', self.__on_button_press_event)
        self.connect('destroy', self.__on_destroy)

        # Enable alpha
        self.__on_screen_changed(self)

        # Create layout on which to place all child widgets
        self.layout = ScalableWidgetContainer()
        self.add(self.layout)
        self.layout.show()

        self.background = None

    def set_has_shadow(self, new_has_shadow):
        """Show or hide the shadow."""
        if new_has_shadow != self.has_shadow:
            self.has_shadow = new_has_shadow
            self.update_shadow_offset()

    def set_shadow_offset(self, new_shadow_offset):
        """Change the shadow offset."""
        if new_shadow_offset != self.shadow_offset:
            self.shadow_offset = new_shadow_offset
            self.update_shadow_offset()

    def set_shadow_color(self, new_shadow_color):
        """Change the colour of the shadow."""
        self.shadow_color = new_shadow_color
        self.update_image()

    def set_canvas_size(self, new_canvas_size):
        """Change the size of the canvas."""
        self.canvas_size = new_canvas_size
        self.set_size(self.get_required_size(*self.canvas_size))

    def do_resize(self, new_width, new_height):
        """Resize the window when size or scale has changed."""
        self.set_size_request(make_int(new_width), make_int(new_height))
        self.update_background(False)
        self.update_shape()

    def do_scale(self, old_scale):
        """Change the scale of child widgets when scale has changed."""
        if self.window:
            self.window.freeze_updates()
        self.layout.set_scale(self.scale)
        if self.window:
            self.window.thaw_updates()

    def update_shape(self):
        """Update the shape of the window."""
        if self.window:
            # Create shape pixmap
            width, height = self.size_request()
            shape = gtk.gdk.Pixmap(self.window, width, height, 1)

            # Create and initialize Cairo context
            ctx = shape.cairo_create()
            cairo_clear(ctx)
            ctx.scale(self.scale, self.scale)

            # Draw to Cairo context and update shape
            self.on_draw_shape(ctx)
            del ctx
            self.window.input_shape_combine_mask(shape, 0, 0)

            # Change the shape of the window if there is no composite extension
            if not self.is_composited():
                self.window.shape_combine_mask(shape, 0, 0)

            del shape

    def update_background(self, repaint=True):
        """Update the background image of the window."""
        if self.window:
            # Create background Pixmap
            width, height = self.size_request()
            if self.background:
                w, h = self.background.get_size()
            else:
                w, h = (0, 0)
            if (w, h) != (width, height):
                del self.background
                self.background = gtk.gdk.Pixmap(self.window, width,
                    height, -1)

            # Create and initialize Cairo context
            ctx = self.background.cairo_create()
            cairo_clear(ctx)
            ctx.scale(self.scale, self.scale)

            # Draw to Cairo context and update background
            self.on_draw(ctx)
            del ctx

            if repaint:
                update_background(self, self.background)

    def update(self):
        """Update the window."""
        if self.window:
            self.window.invalidate_rect(None, True)

    def __on_map(self, widget, event):
        """Update the shape and background when the window is mapped. This
        should really be done when the window is realized, but then the child
        widgets have not been realized."""
        if self.background is None:
            self.update_shape()
            self.update_background()

    def __on_size_allocate(self, widget, event):
        """Update the shape and background."""
        self.update_shape()
        self.update_background()

    def __on_screen_changed(self, widget, screen=None):
        """Set the colormap for the window"""
        if not screen:
            screen = self.get_screen()
        cm = screen.get_rgba_colormap()
        if not cm:
            cm = screen.get_rgb_colormap()
        if self.is_composited() and self.window:
            self.window.shape_combine_mask(None, 0, 0)
        self.set_colormap(cm)

    def __on_button_press_event(self, widget, event):
        """Called when the mouse button is pressed."""
        if event.window == self.window:
            if event.button == 1:
                self.begin_move_drag(event.button, int(event.x_root),
                    int(event.y_root), event.time)
            elif event.button == 3:
                menu = self.make_menu()
                if menu:
                    menu.popup(None, None, None, event.button, event.time)
            else:
                return False
            return True
        return False

    def __on_destroy(self, widget):
        del self.background

    def on_scale(self, oldscale):
        """Called when the widget has been rescaled."""
        pass

    def on_draw(self, ctx):
        """Draw the window."""
        ctx.push_group()
        self.on_draw_background(ctx)
        window = ctx.pop_group()

        # Draw shadow
        if self.is_composited() and self.has_shadow:
            ctx.save()
            ctx.translate(*self.get_shadow_offset())
            if self.SHADOW_BLUR_QUALITY > 2:
                ctx.set_source_rgba(self.shadow_color[0], self.shadow_color[1],
                    self.shadow_color[2],
                    self.shadow_color[3] / self.SHADOW_BLUR_QUALITY)
                for i in xrange(self.SHADOW_BLUR_QUALITY):
                    a = pi * 2 * i / self.SHADOW_BLUR_QUALITY
                    d = (self.SHADOW_BLUR_RADIUS * cos(a),
                        self.SHADOW_BLUR_RADIUS * sin(a))
                    ctx.save()
                    ctx.translate(*d)
                    ctx.mask(window)
                    ctx.restore()
            else:
                ctx.set_source_rgba(*self.shadow_color)
                ctx.mask(window)
            ctx.restore()

        # Draw window
        ctx.translate(*self.get_window_offset())
        ctx.set_source(window)
        ctx.paint()

    def on_draw_shape(self, ctx):
        """Draw the shape."""
        ctx.translate(*self.get_window_offset())
        self.on_draw_background(ctx)

    def on_draw_background(self, ctx):
        """Draw the background of the window."""
        pass

    def put_child(self, child, x, y):
        """Put a child on the layout while respecting the shadow offset."""
        d = self.get_window_offset()
        child.canvas_position = (x, y)
        self.layout.put_scaled(child, x + d[0], y + d[1])

    def move_child(self, child, x, y):
        """Move a child on the layout while respecting the shadow offset."""
        d = self.get_window_offset()
        child.canvas_position = (x, y)
        self.layout.move_scaled(child, x + d[0], y + d[1])


class WWWLink(gtk.EventBox, Scalable):
    """This class creates a label that looks like a link."""

    # Public properties
    text = ''
    url = ''
    font_size = 12000

    def update(self):
        """Update the widget."""
        if self.window:
            self.window.invalidate_rect(None, True)

    def update_text(self):
        self.__label.set_markup(
            '<span foreground="blue" underline="single" size="%i">%s</span>' %
            (int(self.font_size * self.scale), self.text))

    def update_url(self):
        self.__tooltip.set_tip(self, self.url)

    def __init__(self, text='', url='', font_size=12000):
        super(WWWLink, self).__init__()

        self.set_app_paintable(True)

        # Connect signals
        self.connect('realize', self.on_realize)
        self.connect('size-allocate', self.on_size_allocate)

        # Create the label
        self.__label = gtk.Label()
        self.__label.set_use_markup(True)
        self.add(self.__label)
        self.__label.show()
        self.__tooltip = gtk.Tooltips()
        self.__label.connect('size-request', self.on_link_size_request)

        # Set and display the URL
        self.url = url
        self.text = text
        self.font_size = font_size

    def set_text(self, new_text):
        """Change the text of the label."""
        self.text = new_text
        self.update_text()

    def set_url(self, new_url):
        self.url = new_url
        self.update_url()

    def on_realize(self, widget):
        super(WWWLink, self).realize()

        # Set a hand cursor
        cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
        self.window.set_cursor(cursor)
        del cursor

    def on_size_allocate(self, widget, event):
        set_background(self, None)

    def on_link_size_request(self, widget, event):
        self.set_size((event.width / self.scale, event.height / self.scale))

    def do_scale(self, old_scale):
        """Called when the widget has been rescaled."""
        self.update_text()

    def do_resize(self, new_width, new_height):
        """Called when the widget has been resized."""
        self.set_size_request(make_int(new_width), make_int(new_height))


class ScalableWidget(gtk.DrawingArea, Scalable):
    """A scalable widget."""
    shape = None

    def __init__(self):
        super(ScalableWidget, self).__init__()

        self.set_flags(self.flags() | gtk.CAN_DEFAULT)
        self.set_app_paintable(True)

        # Connect signals
        self.connect('realize', self.on_realize)
        self.connect('expose-event', self.on_expose_event)
        self.connect('size-allocate', self.on_size_allocate)

        self.shape = None

    def do_resize(self, new_width, new_height):
        """Resize the widget when size or scale has changed."""
        self.set_size_request(make_int(new_width), make_int(new_height))
        self.update_shape()

    def do_scale(self, old_scale):
        """Send on_scale notification when scale has changed."""
        self.on_scale(old_scale)

    def update_shape(self):
        """Update the shape of the window."""
        if self.window:
            width, height = self.size_request()
            del self.shape
            self.shape = gtk.gdk.Pixmap(self.window, width, height, 1)
            ctx = self.shape.cairo_create()
            cairo_clear(ctx)
            ctx.scale(self.scale, self.scale)
            self.on_draw_shape(ctx)
            self.window.input_shape_combine_mask(self.shape, 0, 0)
            del ctx

    def update(self):
        """Update the widget."""
        if self.window:
            self.window.invalidate_rect(None, True)

    def on_realize(self, widget):
        """Update the shape of the widget when it is realized."""
        set_background(self, None)
        self.update_shape()

    def on_expose_event(self, widget, event):
        """Draw the widget."""
        if self.window:
            ctx = self.window.cairo_create()
            ctx.rectangle(event.area)
            ctx.clip()
            ctx.scale(self.scale, self.scale)
            ctx.set_operator(cairo.OPERATOR_OVER)
            self.on_draw(ctx)
            del ctx

    def on_size_allocate(self, widget, event):
        """Update the shape and background."""
        self.update_shape()
        set_background(self, None)
        self.update()

    def on_scale(self, oldscale):
        """Handle on_scale notification."""
        pass

    def on_draw(self, ctx):
        """Handle on_draw notification."""
        pass

    def on_draw_shape(self, ctx):
        """Handle on_draw_shape notification."""
        pass


class Ticker(ScalableWidget):
    """A ticker animation."""
    TICK_RESOLUTION = 100
    OPACITY_THRESHOLD = 0.05
    OPACITY_VELOCITY = 1.5
    TICKS = 10
    TICK_HEIGHT = 0.5
    TICK_COLORS = (
        (0.4, 0.5, 0.4, 0.0),
        (0.3, 0.8, 0.3, 1.0))

    def update_ticking(self):
        """Show or hide the animation."""
        if not self.__timer and self.ticking:
            self.__opacity = self.OPACITY_THRESHOLD
            self.__timer = gobject.timeout_add(self.TICK_RESOLUTION,
                self.on_timer)

        self.update()

    def __init__(self, size):
        """Create a new ticker displaying image."""
        super(Ticker, self).__init__()
        self.__timer = None
        self.__angle = 0.0
        self.__opacity = 0.0
        self.__timer = None
        self.ticking = False
        self.set_size(size)

    def set_ticking(self, new_ticking):
        if self.ticking != new_ticking:
            self.ticking = new_ticking
            self.update_ticking()

    def on_draw(self, ctx):
        if self.__opacity == 0.0:
            return

        ctx.translate(float(self.rsize[0]) / 2, float(self.rsize[1]) / 2)
        ctx.rotate(float(self.__angle))
        ctx.scale(*self.rsize)

        for i in xrange(self.TICKS):
            t = float(i) / self.TICKS
            ctx.rotate(2 * pi / self.TICKS)
            ctx.arc(0.0, 0.0,
                0.5,
                0.0, pi / self.TICKS)
            ctx.arc_negative(0.0, 0.0,
                0.5 - self.TICK_HEIGHT / 2.0,
                pi / self.TICKS, 0.0)
            ctx.close_path()
            color = map(lambda c1, c2: c1 + (c2 - c1) * t, *self.TICK_COLORS)
            color[3] = color[3] * self.__opacity
            ctx.set_source_rgba(*color)
            ctx.fill()

    def on_timer(self):
        """Callback called when the timer has been triggered."""
        cancel = False
        if self.ticking:
            if self.__opacity < 1.0:
                self.__opacity *= self.OPACITY_VELOCITY
            else:
                self.__opacity = 1.0
        elif not self.ticking:
            if self.__opacity < self.OPACITY_THRESHOLD:
                self.__timer = None
                self.__opacity = 0.0
                self.__timer = None
                cancel = True
            else:
                self.__opacity /= self.OPACITY_VELOCITY
        self.__angle += 2 * pi / self.TICKS
        self.update()

        return not cancel
