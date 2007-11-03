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


//-----------------------------------------------------
//Adapted from the stack applet taken from awn core => I think it need to be move to libawn so everybody can use it


/**
 * Get the decimal value of a hex value
 */
int 
getdec(char hexchar)
{
	if ((hexchar >= '0') && (hexchar <= '9'))
		return hexchar - '0';
		
	if ((hexchar >= 'A') && (hexchar <= 'F'))
		return hexchar - 'A' + 10;
	
	if ((hexchar >= 'a') && (hexchar <= 'f'))
		return hexchar - 'a' + 10;

	g_warning("probleme couleur");
	return -1; // Wrong character
}

/**
 * Convert a HexColor (including alpha) to a FloatColor
 */
void 
hex2float(char* HexColor, float* FloatColor)
{
	gchar	*HexColorPtr = HexColor;
	gint	i;

	for (i = 0; i < 4; i++)
	{
		gint IntColor = (getdec(HexColorPtr[0]) * 16) + getdec(HexColorPtr[1]);
		FloatColor[i] = (gfloat) IntColor / 255.0;
		HexColorPtr += 2;
	}
}

/**
 * Get a color from a GConf key
 */
void
convert_color (AwnColor *color, const gchar *str_color)
{
	gfloat	colors[4];
	
	hex2float (str_color, colors);
		
	color->red = colors[0];
	color->green = colors[1];
	color->blue = colors[2];
	color->alpha = colors[3];
}
//----------------------------------------


#ifdef HAVE_SVG
	// Adapted from kiba-dock
	gboolean
	awn_load_svg (RsvgHandle **handle, char* path, char* theme, char* file_name, GError **error)
	{
		gchar* path_file = g_strdup_printf ( "%s%s/%s", path, theme, file_name);
		
		if ((char*)path_file == NULL || strstr ((char*)path_file, ".svg") == NULL)
			return FALSE;
		
		if (*handle != NULL)
			rsvg_handle_free (*handle);
			
		if (*error != NULL)
			*error = NULL;

		*handle = rsvg_handle_new_from_file (path_file, NULL);
		if (*error != NULL)
		{
			fprintf (stderr, "Failed to load Svg Icon for applet clock\nError");	// : %s\n", (*error)->message);
			g_clear_error (error);
			return FALSE;
		}
		if (handle != NULL)
		{
			//rsvg_handle_set_size_callback (*handle, rsvg_resize_func, object, NULL);
			return TRUE;
		}

		*handle = NULL;
		g_warning("Erreur chargement fichier svg : %s\n", path_file);
		return FALSE;
	}
#endif

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

