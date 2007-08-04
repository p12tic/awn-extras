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
 
/*
 *
 * There are parts of code takes from kiba-dock project
 *
 */

#include "clock-applet.h"
#include "utils.h"

//From kiba-dock
void
convert_color (const char *html_color, double *r, double *g, double *b)
{
	int red,green,blue;
	sscanf (html_color, "#%02X%02X%02X", &red, &green, &blue);
	*r = (double) red   / 256;
	*g = (double) green / 256;
	*b = (double) blue  / 256;
}

/*gboolean
awn_load_png (gchar *icon, GdkPixbuf **pixbuf, GError **error)
{
  GtkIconInfo *icon_info = NULL;
  gchar       *path, *suffix;

  if (icon == NULL)
    return FALSE;

  if (*pixbuf != NULL)
    g_object_unref (*pixbuf);

  /*if (!object->size)
    object->size = object->normal_size;

  object->buffer_size = object->normal_size;/

  if (strstr (icon, "svg")  != NULL)
  {
    g_message ("Cant handle %s\n" "When u wanna use svgs u need svg support in cairo", object->name);

    *pixbuf = NULL;

    return FALSE;
  }

  // try png with absolute path
  g_clear_error (error);
  *pixbuf = gdk_pixbuf_new_from_file_at_size (icon, object->buffer_size, -1, error);
  if (*pixbuf != NULL)
    return TRUE;

  // try png at /usr/share/pixmaps path
  g_clear_error (error);
  path = g_strdup_printf (PIXMAP_PATH "/%s", icon);
  *pixbuf = gdk_pixbuf_new_from_file_at_size (path, object->buffer_size, -1, error);
  if (*pixbuf != NULL)
  {
    g_free (path);
    return TRUE;
  }

  path = NULL;
  g_clear_error (error);
  if (g_file_test ("/usr/share/icons/hicolor/48x48/apps", G_FILE_TEST_IS_DIR))
    path = g_strdup_printf ("/usr/share/icons/hicolor/48x48/apps/%s.png", icon);
  if (path != NULL)
  {
    *pixbuf = gdk_pixbuf_new_from_file_at_size (path, object->buffer_size, -1, error);

    if (*pixbuf != NULL)
    {
      g_free (path);
      return TRUE;
    }
  }

  // try kde dirs
  path = NULL;
  g_clear_error (error);
  if (g_file_test ("/usr/kde/3.5/share/icons/hicolor/48x48/apps", G_FILE_TEST_IS_DIR))
    path = g_strdup_printf ("/usr/kde/3.5/share/icons/hicolor/48x48/apps/%s.png", icon);
  else if (g_file_test ("/usr/kde/3.4/share/icons/hicolor/48x48/apps", G_FILE_TEST_IS_DIR))
    path = g_strdup_printf ("/usr/kde/3.4/share/icons/hicolor/48x48/apps/%s.png", icon);
  if (path != NULL)
  {
    *pixbuf = gdk_pixbuf_new_from_file_at_size (path, object->buffer_size, -1, error);

    if (*pixbuf != NULL)
    {
      g_free (path);
      return TRUE;
    }
  }

  if (path != NULL)
    g_free (path);

  // try png from icon theme
  g_clear_error (error);
  icon_info = gtk_icon_theme_lookup_icon (gtk_icon_theme_get_default (), icon, object->buffer_size, 0);
  if (icon_info != NULL)
  {
    *pixbuf = gdk_pixbuf_new_from_file_at_size (gtk_icon_info_get_filename (icon_info), object->buffer_size, -1, error);
    gtk_icon_info_free (icon_info);
  }
  if (*pixbuf != NULL)
    return TRUE;

  // try png at
  g_clear_error (error);
  suffix = strstr (icon, ".png");
  if (suffix == NULL)
    return FALSE;
  *suffix = '\0';
  icon_info = gtk_icon_theme_lookup_icon (gtk_icon_theme_get_default (), icon, object->buffer_size, 0);
  if (icon_info != NULL)
  {
    *pixbuf = gdk_pixbuf_new_from_file_at_size (gtk_icon_info_get_filename (icon_info), object->buffer_size, -1, error);
    gtk_icon_info_free(icon_info);
  }
  if (error != NULL)
    g_clear_error (error);
  if (*pixbuf != NULL)
    return TRUE;

  return FALSE;
}*/


#ifdef HAVE_SVG
	//From kiba-dock
	gboolean
	awn_load_svg (char* path, RsvgHandle **handle, GError **error)
	{
		if (path == NULL || strstr (path, ".svg") == NULL)
			return FALSE;

		if (*handle != NULL)
			rsvg_handle_free (*handle);

		/*if (!object->size)
			object->size = object->normal_size;

		object->buffer_size = object->normal_size;*/

		*handle = rsvg_handle_new_from_file (path, NULL);
		if (*error != NULL)
		{
			fprintf (stderr, "Failed to load Svg Icon for launcher %s\n" "notifications: %s\n", "", (*error)->message);
			g_clear_error (error);
			return FALSE;
		}
		if (handle != NULL)
		{
			//rsvg_handle_set_size_callback (*handle, rsvg_resize_func, object, NULL);
			return TRUE;
		}

		*handle = NULL;

		return FALSE;
	}
#endif
