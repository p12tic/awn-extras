

#ifndef _CAIRO_MISC
#define _CAIRO_MISC

#include <libdesktop-agnostic/fdo.h>
#include <gtk/gtk.h>

DesktopAgnosticFDODesktopEntry * get_desktop_entry (gchar * desktop_file);

void _launch (GtkMenuItem *menu_item,gchar * desktop_file);

GtkWidget * get_gtk_image (gchar * icon_name);

#endif /* _CAIRO_MISC */