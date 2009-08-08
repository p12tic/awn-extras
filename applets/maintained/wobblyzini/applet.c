/*
 * Copyright (c) 2007 Nicolas de BONFILS
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include <libawn/awn-applet.h>
#include "config.h"

#include "wobblyziniapplet.h"

#ifdef X_EVENT_WATCHING
 #include <X11/Xlib.h>
#endif

static gboolean
_button_clicked_event (GtkWidget      *widget,
                       GdkEventButton *event,
                       AwnApplet *applet)
{
  static GtkWidget *menu=NULL;
  if (event->button == 3)
  {
    if (!menu)
    {
      menu = awn_applet_create_default_menu (applet);
    }
    gtk_menu_set_screen (GTK_MENU (menu), NULL);
    gtk_menu_popup (GTK_MENU (menu), NULL, NULL, NULL, NULL,
                    event->button, event->time);
  }
  return TRUE;
}

GdkFilterReturn filter_func(GdkXEvent *xevent, GdkEvent *event, gpointer data)
{
#ifdef X_EVENT_WATCHING
  static const gchar* event_names[] = {
    "undefined",
    "undefined",
    "KeyPress",
    "KeyRelease",
    "ButtonPress",
    "ButtonRelease",
    "MotionNotify",
    "EnterNotify",
    "LeaveNotify",
    "FocusIn",
    "FocusOut",
    "KeymapNotify",
    "Expose",
    "GraphicsExpose",
    "NoExpose",
    "VisibilityNotify",
    "CreateNotify",
    "DestroyNotify",
    "UnmapNotify",
    "MapNotify",
    "MapRequest",
    "ReparentNotify",
    "ConfigureNotify",
    "ConfigureRequest",
    "GravityNotify",
    "ResizeRequest",
    "CirculateNotify",
    "CirculateRequest",
    "PropertyNotify",
    "SelectionClear",
    "SelectionRequest",
    "SelectionNotify",
    "ColormapNotify",
    "ClientMessage",
    "MappingNotify"
  };

  XEvent *xe = (XEvent *) xevent;
  g_debug ("%d -> %s (win: %d)", xe->type, event_names[xe->type], xe->xany.window);
  if (xe->type == PropertyNotify) {
    GdkAtom atom = gdk_x11_xatom_to_atom(xe->xproperty.atom);
    g_debug (" Atom: %s (%s)", gdk_atom_name(atom), xe->xproperty.state == PropertyNewValue ? "PropertyNewValue" : "PropertyDelete");
  } else if (xe->type == ClientMessage) {
    GdkAtom atom = gdk_x11_xatom_to_atom(xe->xclient.message_type);
    g_debug (" Atom: %s", gdk_atom_name(atom));
  }

#endif

  return GDK_FILTER_CONTINUE;
}

// entry method
AwnApplet*
awn_applet_factory_initp (const gchar *name, const gchar *uid, gint panel_id)
{
	AwnApplet *applet;
	WobblyZini *wobblyzini;

	// initialize the applet
	applet = awn_applet_new (name, uid, panel_id);
	// our initialize
	wobblyzini = wobblyzini_applet_new(applet);
	// right-click handling
	g_signal_connect (G_OBJECT (applet), "button-press-event",
	                  G_CALLBACK (_button_clicked_event), applet);

  // just for debugging X stuff
  gdk_window_add_filter(NULL, filter_func, NULL);

	return applet;
}

