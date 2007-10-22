#ifndef _ENGINES_H_
#define _ENGINES_H_

#include <gtk/gtk.h>
#include <glib.h>


//typedef void (*ActionInvokedCb)(GtkWindow *nw, const char *key);
typedef void (*UrlClickedCb)(GtkWindow *nw, const char *url);

GtkWindow *create_notification(UrlClickedCb url_clicked_cb);
void destroy_notification(GtkWindow *nw);
void show_notification(GtkWindow *nw);
void hide_notification(GtkWindow *nw);
void set_notification_hints(GtkWindow *nw, GHashTable *hints);
void set_notification_timeout(GtkWindow *nw, glong timeout);
void notification_tick(GtkWindow *nw, glong remaining);
void set_notification_text(GtkWindow *nw, const char *summary,
								 const char *body);
void set_notification_icon(GtkWindow *nw, GdkPixbuf *pixbuf);
void set_notification_arrow(GtkWidget *nw, gboolean visible, int x, int y);

void add_notification_action(GtkWindow *nw, const char *label,
								   const char *key, GCallback cb);
void clear_notification_actions(GtkWindow *nw);
void move_notification(GtkWidget *nw, int x, int y);

		  				 

#endif /* _ENGINES_H_ */
