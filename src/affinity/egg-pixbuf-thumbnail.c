/* Egg Libraries: egg-pixbuf-thumbnail.c
 * 
 * Copyright (c) 2004 James M. Cape <jcape@ignore-your.tv>
 * Copyright (c) 2002 Red Hat, Inc.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifdef HAVE_CONFIG_H
# include <config.h>
#endif /* HAVE_CONFIG_H */

#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>
#include <stdio.h>
#include <fcntl.h>

#include <stdlib.h>
#include <string.h>

#include <glib/gi18n.h>
#include <glib/gstdio.h>
#ifdef LIBAWN_USE_XFCE
#include <exo/exo.h>
#else
#include <glib/gchecksum.h>
#endif

#include <gdk-pixbuf/gdk-pixbuf-io.h>

#include "egg-pixbuf-thumbnail.h"


/* **************** *
 *  Private Macros  *
 * **************** */

/* 30 days in seconds */
#define EXPIRATION_TIME		2592000

/* Metadata Keys */
/* Standard */
#define THUMB_URI_KEY		"tEXt::Thumb::URI"
#define THUMB_MTIME_KEY		"tEXt::Thumb::MTime"
#define THUMB_MIME_TYPE_KEY	"tEXt::Thumb::Mimetype"
#define THUMB_FILESIZE_KEY	"tEXt::Thumb::Size"
#define THUMB_WIDTH_KEY		"tEXt::Thumb::Image::Width"
#define THUMB_HEIGHT_KEY	"tEXt::Thumb::Image::Height"
#define THUMB_PAGES_KEY		"tEXt::Thumb::Document::Pages"
#define THUMB_LENGTH_KEY	"tEXt::Thumb::Movie::Length"
#define THUMB_DESCRIPTION_KEY	"tEXt::Description"
#define THUMB_SOFTWARE_KEY	"tEXt::Software"

/* Used by failed creation attempts */
#define THUMB_ERROR_DOMAIN_KEY	"tEXt::X-GdkPixbuf::FailDomain"
#define FILE_ERROR_NAME		"file"
#define PIXBUF_ERROR_NAME	"pixbuf"
#define THUMB_ERROR_CODE_KEY	"tEXt::X-GdkPixbuf::FailCode"
#define THUMB_ERROR_MESSAGE_KEY	"tEXt::X-GdkPixbuf::FailMessage"

/* Misc Strings */
#define NORMAL_DIR_NAME		"normal"
#define LARGE_DIR_NAME		"large"
#define FAIL_DIR_NAME		"fail"
#define APP_DIR_NAME		"gdk-pixbuf-2"
#define THUMB_SOFTWARE_VALUE	"GdkPixbuf"


#define THUMBNAIL_DATA_QUARK	(thumbnail_data_get_quark ())
#define SIZE_TO_DIR(size) ({\
  const gchar *__r; \
  if (size == EGG_PIXBUF_THUMBNAIL_NORMAL) \
    __r = NORMAL_DIR_NAME; \
  else if (size == EGG_PIXBUF_THUMBNAIL_LARGE) \
    __r = LARGE_DIR_NAME; \
  else \
    __r = NULL; \
  __r; \
})


/* ******************** *
 *  Private Structures  *
 * ******************** */

typedef struct
{
  /* Required */
  gint size;
  gchar *uri;
  time_t mtime;

  /* Optional Generic */
  gssize filesize;
  gchar *mime_type;
  gchar *description;
  gchar *software;

  /* Optional Image */
  gint image_width;
  gint image_height;

  /* Optional Document */
  gint document_pages;

  /* Optional Movie */
  time_t movie_length;
}
ThumbnailData;

typedef struct
{
  gint orig_width;
  gint orig_height;
  gint size;
}
ImageInfo;


/* ************************* *
 *  ThumbnailData Functions  *
 * ************************* */

static GQuark
thumbnail_data_get_quark (void)
{
  static GQuark quark = 0;

  if (G_UNLIKELY (quark == 0))
    quark = g_quark_from_static_string ("egg-pixbuf-thumbnail-data");

  return quark;
}

static void
thumbnail_data_free (ThumbnailData *data)
{
  if (!data)
    return;

  g_free (data->uri);
  g_free (data->mime_type);
  g_free (data->description);
  g_free (data->software);
  g_free (data);
}

static ThumbnailData *
get_thumbnail_data (GdkPixbuf *thumbnail)
{
  return g_object_get_qdata (G_OBJECT (thumbnail), THUMBNAIL_DATA_QUARK);
}

static ThumbnailData *
ensure_thumbnail_data (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  data = get_thumbnail_data (thumbnail);

  if (!data)
    {
      data = g_new (ThumbnailData, 1);
      data->uri = NULL;
      data->mtime = -1;
      data->size = EGG_PIXBUF_THUMBNAIL_UNKNOWN;
      data->filesize = -1;
      data->mime_type = NULL;
      data->description = NULL;
      data->software = NULL;
      data->image_width = -1;
      data->image_height = -1;
      data->document_pages = -1;
      data->movie_length = -1;

      g_object_set_qdata_full (G_OBJECT (thumbnail), THUMBNAIL_DATA_QUARK, data,
			       (GDestroyNotify) thumbnail_data_free);
    }

  return data;
}

static gboolean
parse_thumbnail_data (GdkPixbuf              *thumbnail,
		      EggPixbufThumbnailSize  size,
		      GError                **error)
{
  ThumbnailData *data;
  const gchar *tmp;
  glong value;
  guint8 data_required;

  data_required = 2;
  data = NULL;

  if (error)
    {
      GQuark domain;

      tmp = gdk_pixbuf_get_option (thumbnail, THUMB_ERROR_DOMAIN_KEY);
      if (tmp)
	domain = g_quark_from_string (tmp);
      else
	domain = g_quark_from_static_string ("egg-pixbuf-thumbnail-error");

      tmp = gdk_pixbuf_get_option (thumbnail, THUMB_ERROR_CODE_KEY);
      if (tmp)
	value = strtol (tmp, NULL, 10);
      else
	value = -1;

      tmp = gdk_pixbuf_get_option (thumbnail, THUMB_ERROR_MESSAGE_KEY);

      *error = g_error_new_literal (domain, value, tmp);
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_URI_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      data->uri = g_strdup (tmp);
      data_required--;
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_MTIME_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      value = strtol (tmp, NULL, 10);
      if (value != G_MAXINT && value != G_MININT)
	{
	  data->mtime = value;
	  data_required--;
	}
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_MIME_TYPE_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      data->mime_type = g_strdup (tmp);
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_DESCRIPTION_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      data->description = g_strdup (tmp);
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_SOFTWARE_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      data->software = g_strdup (tmp);
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_FILESIZE_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      value = strtol (tmp, NULL, 10);
      if (value != G_MAXINT && value != G_MININT)
	data->filesize = value;
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_WIDTH_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      value = strtol (tmp, NULL, 10);
      if (value != G_MAXINT && value != G_MININT)
	data->image_width = value;
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_HEIGHT_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      value = strtol (tmp, NULL, 10);
      if (value != G_MAXINT && value != G_MININT)
	data->image_height = value;
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_PAGES_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      value = strtol (tmp, NULL, 10);
      if (value != G_MAXINT && value != G_MININT)
	data->document_pages = value;
    }

  tmp = gdk_pixbuf_get_option (thumbnail, THUMB_LENGTH_KEY);
  if (tmp)
    {
      data = ensure_thumbnail_data (thumbnail);
      value = strtol (tmp, NULL, 10);
      if (value != G_MAXINT && value != G_MININT)
	data->movie_length = value;
    }

  if (!data_required)
    data->size = size;

  return (!data_required);
}


/* *************************************** *
 *  Global Thumbnails Directory Functions  *
 * *************************************** */

static gboolean
ensure_one_dir (const gchar *path,
		GError     **error)
{
  if (!g_file_test (path, G_FILE_TEST_IS_DIR) && g_mkdir (path, 0700) < 0)
    {
      gchar *utf8_path;

      utf8_path = g_filename_to_utf8 (path, -1, NULL, NULL, NULL);
      g_set_error (error, G_FILE_ERROR, g_file_error_from_errno (errno),
		   _("Error creating directory `%s': %s"), utf8_path,
		   g_strerror (errno));
      g_free (utf8_path);
      return FALSE;
    }

  return TRUE;
}

static gboolean
ensure_thumbnail_dirs (GError **error)
{
  gchar *path, *tmp;

  path = g_build_filename (g_get_home_dir (), ".thumbnails", NULL);
  if (!ensure_one_dir (path, error))
    {
      g_free (path);
      return FALSE;
    }

  tmp = path;
  path = g_build_filename (tmp, NORMAL_DIR_NAME, NULL);
  if (!ensure_one_dir (path, error))
    {
      g_free (path);
      g_free (tmp);
      return FALSE;
    }

  g_free (path);

  path = g_build_filename (tmp, LARGE_DIR_NAME, NULL);
  if (!ensure_one_dir (path, error))
    {
      g_free (path);
      g_free (tmp);
      return FALSE;
    }

  g_free (path);

  path = g_build_filename (tmp, FAIL_DIR_NAME, NULL);
  if (!ensure_one_dir (path, error))
    {
      g_free (path);
      g_free (tmp);
      return FALSE;
    }

  g_free (path);

  path = g_build_filename (tmp, FAIL_DIR_NAME, APP_DIR_NAME, NULL);
  if (!ensure_one_dir (path, error))
    {
      g_free (path);
      g_free (tmp);
      return FALSE;
    }

  g_free (tmp);
  g_free (path);
  return TRUE;
}


/* ****************************** *
 *  Thumbnail Creation Functions  *
 * ****************************** */

static void
loader_size_prepared_cb (GdkPixbufLoader *loader,
			 gint             width,
			 gint             height,
			 gpointer         user_data)
{
  ImageInfo *info;

  info = user_data;
  info->orig_width = width;
  info->orig_height = height;

  if (info->size > 0 && (width > info->size || height > info->size))
    {
      gdouble scale;

      if (width > height)
	scale = (gdouble) info->size / width;
      else
	scale = (gdouble) info->size / height;

      gdk_pixbuf_loader_set_size (loader, width * scale, height * scale);
    }
}

static GdkPixbuf *
load_image_at_max_size (const gchar *filename,
			ImageInfo   *info,
			gchar      **mime_type,
			GError     **error)
{
  GdkPixbuf *retval;
  GdkPixbufLoader *loader;
  FILE *f;
  gsize result;
  guchar buffer[8192];

  f = g_fopen (filename, "rb");
  if (!f)
    {
      gchar *display_name;

      display_name = g_filename_display_name (filename);
      g_set_error (error, G_FILE_ERROR, g_file_error_from_errno (errno),
		   _("Error opening `%s': %s"), display_name,
		   g_strerror (errno));
      g_free (display_name);

      return NULL;
    }

  loader = gdk_pixbuf_loader_new ();
  g_signal_connect (loader, "size-prepared",
		    G_CALLBACK (loader_size_prepared_cb), info);

  result = fread (buffer, 1, sizeof (buffer), f);
  if (!result)
    {
      gchar *display_name;

      display_name = g_filename_display_name (filename);
      g_set_error (error, G_FILE_ERROR, g_file_error_from_errno (errno),
		   _("Error reading `%s': file contains no data."),
		   display_name);
      g_free (display_name);
      fclose (f);
      return NULL;
    }

  fseek (f, 0, SEEK_SET);

  do
    {
      result = fread (buffer, 1, sizeof (buffer), f);

      /* Die on read() error. */
      if (!result && ferror (f))
	{
	  gchar *display_name;

	  gdk_pixbuf_loader_close (loader, NULL);
	  fclose (f);
	  g_object_unref (loader);

	  display_name = g_filename_display_name (filename);
	  g_set_error (error, G_FILE_ERROR, g_file_error_from_errno (errno),
		       _("Error reading `%s': %s"), display_name,
		       g_strerror (errno));
	  g_free (display_name);
	  return NULL;
	}
      /* Die on loader error. */
      else if (!gdk_pixbuf_loader_write (loader, buffer, result, error))
	{
	  gdk_pixbuf_loader_close (loader, NULL);
	  fclose (f);
	  g_object_unref (loader);
	  return NULL;
	}
    }
  while (!feof (f));

  fclose (f);

  if (!gdk_pixbuf_loader_close (loader, error))
    {
      g_object_unref (loader);
      return NULL;
    }

  retval = gdk_pixbuf_loader_get_pixbuf (loader);

  if (!retval)
    {
      gchar *display_name;

      display_name = g_filename_display_name (filename);

      g_set_error (error,
		   GDK_PIXBUF_ERROR,
		   GDK_PIXBUF_ERROR_FAILED,
		   _("Failed to load image '%s': reason not known, probably a corrupt image file"),
		   display_name ? display_name : "???");
      g_free (display_name);
    }
  else
    {
      g_object_ref (retval);

      if (mime_type)
	{
	  GdkPixbufFormat *format;
	  gchar **mime_types;

	  format = gdk_pixbuf_loader_get_format (loader);
	  mime_types = gdk_pixbuf_format_get_mime_types (format);
	  if (mime_types && mime_types[0])
	    *mime_type = g_strdup (mime_types[0]);
	  g_strfreev (mime_types);
	}
    }

  g_object_unref (loader);

  return retval;
}

/**
 * egg_pixbuf_get_thumbnail_for_file:
 * @filename: the path to the original file.
 * @size: the desired size of the thumnail.
 * @error: a pointer to a location to store errors in.
 * 
 * Convenience function which first checks if a failure attempt for @filename
 * exists. If it does, @error will be set to the reason for that failure. If it
 * does not, this function attempts to load the thumbnail for @filename at
 * @size. If that load fails, this function will attempt to create a new
 * thumbnail. If creating a new thumbnail fails, then a new failure attempt
 * will be saved.
 * 
 * In other words, this function handles all the intricasies of thumbnailing
 * local images internally, and you should see if using it makes sense before
 * trying more complicated schemes.
 * 
 * Returns: the thumbnail of @filename, or %NULL.
 * 
 * Since: 2.6
 **/
GdkPixbuf *
egg_pixbuf_get_thumbnail_for_file (const gchar            *filename,
				   EggPixbufThumbnailSize  size,
				   GError                **error)
{
  return egg_pixbuf_get_thumbnail_for_file_at_size (filename, (gint)size, error);
}

GdkPixbuf *
egg_pixbuf_get_thumbnail_for_file_at_size (const gchar            *filename,
				           gint                    size,
				           GError                **error)
{
  GdkPixbuf *retval;
  gchar *uri;
  struct stat st;

  g_return_val_if_fail (filename != NULL && filename[0] == '/', NULL);
  g_return_val_if_fail (size > 0 || size == EGG_PIXBUF_THUMBNAIL_UNKNOWN, NULL);
  g_return_val_if_fail (error == NULL || *error == NULL, FALSE);

  if (g_stat (filename, &st) < 0)
    {
      gchar *display_name;

      display_name = g_filename_display_name (filename);
      g_set_error (error, G_FILE_ERROR, g_file_error_from_errno (errno),
		   _("Error verifying `%s': %s"), display_name,
		   g_strerror (errno));
      g_free (display_name);
      return NULL;
    }

  if (!S_ISREG (st.st_mode) && !S_ISLNK (st.st_mode))
    {
      gchar *display_name;

      display_name = g_filename_display_name (filename);
      g_set_error (error, G_FILE_ERROR, g_file_error_from_errno (errno),
		   _("Error reading `%s': file is not a regular file or symbolic link."),
		   display_name);
      g_free (display_name);
      return NULL;
    }

  uri = g_filename_to_uri (filename, NULL, error);
  if (!uri)
    {
      return NULL;
    }

  if (egg_pixbuf_has_failed_thumbnail (uri, st.st_mtime, error))
    {
      g_free (uri);
      return NULL;
    }

  retval = egg_pixbuf_load_thumbnail (uri, st.st_mtime, size);
  if (!retval)
    {
      GError *real_error;
      gchar *mime_type;
      ImageInfo info;

      info.size = size;
      mime_type = NULL;
      real_error = NULL;

      retval = load_image_at_max_size (filename, &info, &mime_type,
				       &real_error);

      if (!retval)
	{
	  /*
	   * Don't save failures for filetypes not supported by GdkPixbuf.
	   * 
	   * I *think* this is the proper way to go, as there's no need to
	   * spill a half-gig of disk space telling the thumbnailing world
	   * that GdkPixbuf doesn't understand "blah/autogen.sh".
	   */
	  if (real_error->domain != GDK_PIXBUF_ERROR ||
	      real_error->code != GDK_PIXBUF_ERROR_UNKNOWN_TYPE)
	    egg_pixbuf_save_failed_thumbnail (uri, st.st_mtime, real_error);

	  if (error != NULL)
	    *error = real_error;
	  else
	    g_error_free (real_error);
	}
      else
	{
	  ThumbnailData *data;

	  data = ensure_thumbnail_data (retval);
	  data->size = size;
	  data->uri = g_strdup (uri);
	  data->mtime = st.st_mtime;
	  data->mime_type = g_strdup (mime_type);
	  data->description = g_strdup (gdk_pixbuf_get_option (retval,
							       THUMB_DESCRIPTION_KEY));
	  data->mime_type = g_strdup (mime_type);
	  data->image_width = info.orig_width;
	  data->image_height = info.orig_height;
	  data->filesize = st.st_size;

	  egg_pixbuf_save_thumbnailv (retval, NULL, NULL, NULL);
	}

      g_free (mime_type);
    }

  g_free (uri);

  return retval;
}

/**
 * egg_pixbuf_load_thumbnail:
 * @uri: the URI of the thumbnailed file.
 * @size: the size of the thumbnail to load.
 * @mtime: the last modified time of @uri, or %-1 if unknown.
 * 
 * Attempts to load the thumbnail for @uri at @size. If the thumbnail for @uri
 * at @size does not already exist, %NULL will be returned.
 * 
 * Returns: the thumbnail pixbuf of @uri at @size which must be un-referenced
 *  with g_object_unref() when no longer needed, or %NULL.
 * 
 * Since: 2.6
 **/
GdkPixbuf *
egg_pixbuf_load_thumbnail (const gchar           *uri,
			   time_t                 mtime,
			   EggPixbufThumbnailSize size)
{
  GdkPixbuf *retval;
  gchar *filename;

  g_return_val_if_fail (uri != NULL && uri[0] != '\0', NULL);
  g_return_val_if_fail (mtime >= 0, NULL);
  g_return_val_if_fail (size == EGG_PIXBUF_THUMBNAIL_NORMAL ||
			size == EGG_PIXBUF_THUMBNAIL_LARGE, NULL);

  filename = egg_pixbuf_get_thumbnail_filename (uri, size);
  retval = gdk_pixbuf_new_from_file (filename, NULL);
  g_free (filename);

  if (retval != NULL &&
      (!parse_thumbnail_data (retval, size, NULL) ||
       !egg_pixbuf_is_thumbnail (retval, uri, mtime)))
    {
      g_object_unref (retval);
      return NULL;
    }

  return retval;
}

/**
 * egg_pixbuf_load_thumbnail_at_size:
 * @uri: the URI of the thumbnailed file.
 * @mtime: the last modified time of @uri, or %-1 if unknown.
 * @pixel_size: the desired pixel size.
 * 
 * Attempts to load the thumbnail for @uri at @size. If the thumbnail for @uri
 * at @size does not already exist, %NULL will be returned.
 * 
 * Returns: the thumbnail pixbuf of @uri at @size which must be un-referenced
 *  with g_object_unref() when no longer needed, or %NULL.
 * 
 * Since: 2.6
 **/
GdkPixbuf *
egg_pixbuf_load_thumbnail_at_size (const gchar *uri,
				   time_t       mtime,
				   gint         pixel_size)
{
  ImageInfo info;
  GdkPixbuf *retval;
  gchar *filename;

  g_return_val_if_fail (uri != NULL && uri[0] != '\0', NULL);
  g_return_val_if_fail (mtime >= 0, NULL);

  if (pixel_size <= EGG_PIXBUF_THUMBNAIL_NORMAL)
    {
      info.size = EGG_PIXBUF_THUMBNAIL_NORMAL;
      filename = egg_pixbuf_get_thumbnail_filename (uri, EGG_PIXBUF_THUMBNAIL_NORMAL);
    }
  else if (pixel_size <= EGG_PIXBUF_THUMBNAIL_LARGE)
    {
      info.size = EGG_PIXBUF_THUMBNAIL_LARGE;
      filename = egg_pixbuf_get_thumbnail_filename (uri, EGG_PIXBUF_THUMBNAIL_LARGE);
    }
  else if (strncmp (uri, "file://", 7) == 0)
    {
      info.size = -1;
      filename = g_strdup (uri + 7);
    }
  else
    {
      info.size = -1;
      filename = egg_pixbuf_get_thumbnail_filename (uri, EGG_PIXBUF_THUMBNAIL_LARGE);
    }

  retval = load_image_at_max_size (filename, &info, NULL, NULL);
  g_free (filename);

  if (retval != NULL &&
      (!parse_thumbnail_data (retval, info.size, NULL) ||
       !egg_pixbuf_is_thumbnail (retval, uri, mtime)))
    {
      g_object_unref (retval);
      return NULL;
    }

  return retval;
}


/* ****************** *
 *  Saving Functions  *
 * ****************** */

static void
collect_save_options (va_list   opts,
                      gchar  ***keys,
                      gchar  ***vals)
{
  gchar *key;
  gchar *val;
  gchar *next;
  gint count;

  count = 0;
  *keys = NULL;
  *vals = NULL;
  
  next = va_arg (opts, gchar*);
  while (next)
    {
      key = next;
      val = va_arg (opts, gchar*);

      ++count;

      /* woo, slow */
      *keys = g_realloc (*keys, sizeof(gchar*) * (count + 1));
      *vals = g_realloc (*vals, sizeof(gchar*) * (count + 1));
      
      (*keys)[count-1] = g_strdup (key);
      (*vals)[count-1] = g_strdup (val);

      (*keys)[count] = NULL;
      (*vals)[count] = NULL;
      
      next = va_arg (opts, gchar*);
    }
}

/**
 * egg_pixbuf_save_thumbnail:
 * @thumbnail: the valid thumbnail pixbuf to save.
 * @error: a location to a pointer to store an error.
 * @Varargs: a %NULL-terminated metadata key/value pair list.
 * 
 * Saves @thumbnail to it's appropriate file. Note that @thumbnail must have
 * it's URI, mtime, and size metadata set before this function is called. Any
 * additional metadata can be saved using the %NULL-terminated
 * variable-arguments list. If an error occurs while saving the thumbnail, a
 * failure thumbnail will be automatically created and saved.
 * 
 * Returns: %TRUE if the thumbnail was successfully saved, %FALSE if it was not.
 * 
 * Since: 2.6
 **/
gboolean
egg_pixbuf_save_thumbnail (GdkPixbuf *thumbnail,
			   GError   **error,
			   ...)
{
  va_list args;
  gboolean retval;
  gchar **keys, **values;

  g_return_val_if_fail (egg_pixbuf_is_thumbnail (thumbnail, NULL, -1), FALSE);
  g_return_val_if_fail (error == NULL || *error == NULL, FALSE);

  keys = NULL;
  values = NULL;

  va_start (args, error);
  collect_save_options (args, &keys, &values);
  va_end (args);

  retval = egg_pixbuf_save_thumbnailv (thumbnail, keys, values, error);

  g_strfreev (values);
  g_strfreev (keys);

  return retval;
}

static gchar **
create_pair_array (const gchar *key,
		   const gchar *value)
{
  gchar **retval;

  retval = g_new (gchar *, 2);
  retval[0] = g_strdup (key);
  retval[1] = g_strdup (value);

  return retval;
}

static inline void
merge_keys_values_and_thumbnail_data (GdkPixbuf   *thumbnail,
				      gchar      **src_keys,
				      gchar      **src_values,
				      gchar     ***dest_keys,
				      gchar     ***dest_values)
{
  ThumbnailData *data;
  GSList *list;
  guint n_pairs, i;
  gchar *tmp;

  data = g_object_get_qdata (G_OBJECT (thumbnail), THUMBNAIL_DATA_QUARK);
  if (!data)
    {
      *dest_keys = g_strdupv (src_keys);
      *dest_values = g_strdupv (src_values);
      return;
    }

  list = g_slist_prepend (NULL, create_pair_array (THUMB_SOFTWARE_KEY,
						   THUMB_SOFTWARE_VALUE));

  if (data->uri)
    list = g_slist_prepend (list, create_pair_array (THUMB_URI_KEY, data->uri));

  if (data->mtime >= 0)
    {
      tmp = g_strdup_printf ("%ld", data->mtime);
      list = g_slist_prepend (list, create_pair_array (THUMB_MTIME_KEY, tmp));
      g_free (tmp);
    }

  if (data->description)
    list = g_slist_prepend (list, create_pair_array (THUMB_DESCRIPTION_KEY,
						     data->description));

  if (data->mime_type)
    list = g_slist_prepend (list, create_pair_array (THUMB_MIME_TYPE_KEY,
						     data->mime_type));

  if (data->software)
    list = g_slist_prepend (list, create_pair_array (THUMB_SOFTWARE_KEY,
						     data->software));

  if (data->filesize > 0)
    {
      tmp = g_strdup_printf ("%" G_GSSIZE_FORMAT, data->filesize);
      list = g_slist_prepend (list, create_pair_array (THUMB_FILESIZE_KEY, tmp));
      g_free (tmp);
    }

  if (data->image_width > 0)
    {
      tmp = g_strdup_printf ("%d", data->image_width);
      list = g_slist_prepend (list, create_pair_array (THUMB_WIDTH_KEY, tmp));
      g_free (tmp);
    }

  if (data->image_height > 0)
    {
      tmp = g_strdup_printf ("%d", data->image_height);
      list = g_slist_prepend (list, create_pair_array (THUMB_HEIGHT_KEY, tmp));
      g_free (tmp);
    }

  if (data->document_pages > 0)
    {
      tmp = g_strdup_printf ("%d", data->document_pages);
      list = g_slist_prepend (list, create_pair_array (THUMB_PAGES_KEY, tmp));
      g_free (tmp);
    }

  if (data->movie_length >= 0)
    {
      tmp = g_strdup_printf ("%ld", data->movie_length);
      list = g_slist_prepend (list, create_pair_array (THUMB_MTIME_KEY, tmp));
      g_free (tmp);
    }

  /* Get a count of the keys in src_keys */
  if (src_keys)
    {
      for (n_pairs = 0; src_keys[n_pairs] != NULL; n_pairs++);
    }
  else
    n_pairs = 0;

  n_pairs += g_slist_length (list);

  *dest_keys = g_new0 (gchar *, n_pairs + 1);
  *dest_values = g_new0 (gchar *, n_pairs + 1);

  if (src_keys)
    {
      for (i = 0; src_keys[i] != NULL; i++)
	{
	  (*dest_keys)[i] = g_strdup (src_keys[i]);
	  (*dest_values)[i] = g_strdup (src_values[i]);
	}
    }
  else
    i = 0;

  while (list)
    {
      gchar **pair;

      pair = list->data;
      (*dest_keys)[i] = pair[0];
      (*dest_values)[i] = pair[1];
      g_free (pair);
      list = g_slist_remove_link (list, list);
      i++;
    }
}

/**
 * egg_pixbuf_save_thumbnailv:
 * @thumbnail: the thumbnail to save.
 * @keys: a NULL-terminated array of metadata keys.
 * @values: a NULL-terminated array of metadata values.
 * @error: a pointer to a location to store errors in.
 * 
 * This function is primarily useful to language bindings. Applications should
 * use egg_pixbuf_save_thumbnail().
 * 
 * Returns: %TRUE if the thumbnail was successfully saved, %FALSE if it was not.
 * 
 * Since: 2.6
 **/
gboolean
egg_pixbuf_save_thumbnailv (GdkPixbuf *thumbnail,
			    gchar    **keys,
			    gchar    **values,
			    GError   **error)
{
  const gchar *uri;
  gchar *filename, *tmp_filename;
  gchar **real_keys, **real_values;
  gint fd;
  gboolean retval;
  GError *real_error;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), FALSE);
  g_return_val_if_fail (egg_pixbuf_is_thumbnail (thumbnail, NULL, -1), FALSE);
  g_return_val_if_fail (error == NULL || *error == NULL, FALSE);

  if (!ensure_thumbnail_dirs (error))
    return FALSE;

  uri = egg_pixbuf_get_thumbnail_uri (thumbnail);
  filename =
    egg_pixbuf_get_thumbnail_filename (uri,
				       egg_pixbuf_get_thumbnail_size (thumbnail));
  tmp_filename = g_strconcat (filename, ".XXXXXX", NULL);

  fd = g_mkstemp (tmp_filename);
  if (fd < 0)
    {
      real_error =
	g_error_new (G_FILE_ERROR,
		     g_file_error_from_errno (errno),
		     _("Error creating temporary thumbnail file for `%s': %s"),
		     uri, g_strerror (errno));
      g_free (tmp_filename);
      g_free (filename);
				  
      egg_pixbuf_save_failed_thumbnail (egg_pixbuf_get_thumbnail_uri (thumbnail),
					egg_pixbuf_get_thumbnail_mtime (thumbnail),
					real_error);
      if (error != NULL)
	*error = real_error;
      else
	g_error_free (real_error);

      return FALSE;
    }
  else
    {
      close (fd);
      chmod (tmp_filename, 0600);
    }

  real_error = NULL;
  merge_keys_values_and_thumbnail_data (thumbnail, keys, values,
					&real_keys, &real_values);
  retval = gdk_pixbuf_savev (thumbnail, tmp_filename, "png",
			     real_keys, real_values, &real_error);
  g_strfreev (real_keys);
  g_strfreev (real_values);

  if (retval)
    rename (tmp_filename, filename);
  else
    {
      egg_pixbuf_save_failed_thumbnail (egg_pixbuf_get_thumbnail_uri (thumbnail),
					egg_pixbuf_get_thumbnail_mtime (thumbnail),
					real_error);

      if (error != NULL)
	*error = real_error;
      else
	g_error_free (real_error);
    }

  g_free (tmp_filename);
  g_free (filename);

  return retval;
}


/* ******************* *
 *  Failure Functions  *
 * ******************* */

/**
 * egg_pixbuf_has_failed_thumbnail:
 * @uri: the URI of the thumbnailed file to check.
 * @mtime: the last modified time of @uri.
 * @error: a pointer to a location to store an error.
 * 
 * Checks to see if creating a thumbnail for @uri which was changed on @mtime
 * has already been tried and failed. If it has, the error which prevented the
 * thumbnail from being created will be stored in @error.
 * 
 * Returns: %TRUE if the thumbnail creation has already failed, %FALSE if it
 *  has not.
 *
 * Since: 2.6
 **/
gboolean
egg_pixbuf_has_failed_thumbnail (const gchar *uri,
				 time_t       mtime,
				 GError     **error)
{
  gchar *md5, *basename, *filename;
  gboolean retval;
  GdkPixbuf *thumb;

  g_return_val_if_fail (uri != NULL && uri[0] != '\0', FALSE);
  g_return_val_if_fail (error == NULL || *error == NULL, FALSE);

  retval = FALSE;
  
#ifdef LIBAWN_USE_XFCE
  md5 = exo_str_get_md5_str (uri);
#else
  md5 = g_compute_checksum_for_string (G_CHECKSUM_MD5, uri, strlen (uri));
#endif
  basename = g_strconcat (md5, ".png", NULL);
  g_free (md5);
  filename = g_build_filename (g_get_home_dir (), ".thumbnails", FAIL_DIR_NAME,
			       APP_DIR_NAME, basename, NULL);
  thumb = gdk_pixbuf_new_from_file (filename, NULL);
  g_free (basename);
  g_free (filename);

  if (thumb)
    {
      retval = (parse_thumbnail_data (thumb, EGG_PIXBUF_THUMBNAIL_UNKNOWN,
				      error) &&
		egg_pixbuf_is_thumbnail (thumb, uri, mtime));
      g_object_unref (thumb);
    }
  else
    retval = FALSE;

  return retval;
}

/**
 * egg_pixbuf_save_failed_thumbnail:
 * @uri: the URI which the thumbnail creation failed for.
 * @mtime: the time that @uri was last modified.
 * @error: the error which occurred while trying to create the thumbnail.
 * 
 * Saves a "failure thumbnail" for the @uri with @mtime. This lets other
 * applications using the EggPixbufThumbnail API know that a thumbnail attempt
 * was tried for @uri when it was modified last at @mtime. The @error parameter
 * lets other applications know exactly why the thumbnail creation failed.
 * 
 * <note>@error must be in either the #G_FILE_ERROR or #GDK_PIXBUF_ERROR
 * domain.</note>
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_save_failed_thumbnail (const gchar  *uri,
				  time_t        mtime,
				  const GError *error)
{
  GdkPixbuf *pixbuf;
  GError *err_ret;
  gchar *md5, *basename, *filename, *tmp_filename, *mtime_str;
  gboolean saved_ok;
  gint fd;

  g_return_if_fail (uri != NULL && uri[0] != '\0');
  g_return_if_fail (error == NULL ||
		    error->domain == G_FILE_ERROR ||
		    error->domain == GDK_PIXBUF_ERROR);

  err_ret = NULL;
  if (!ensure_thumbnail_dirs (&err_ret))
    {
      g_warning ("%s", err_ret->message);
      g_error_free (err_ret);
      return;
    }

#ifdef LIBAWN_USE_XFCE
  md5 = exo_str_get_md5_str (uri);
#else
  md5 = g_compute_checksum_for_string (G_CHECKSUM_MD5, uri, strlen (uri));
#endif
  basename = g_strconcat (md5, ".png", NULL);
  g_free (md5);
  filename = g_build_filename (g_get_home_dir (), ".thumbnails", FAIL_DIR_NAME,
			       APP_DIR_NAME, basename, NULL);
  g_free (basename);

  tmp_filename = g_strconcat (filename, ".XXXXXX", NULL);
  fd = g_mkstemp (tmp_filename);
  if (fd < 0)
    {
      g_free (tmp_filename);
      g_free (filename);
      return;
    }
  else
    close (fd);

  pixbuf = gdk_pixbuf_new (GDK_COLORSPACE_RGB, TRUE, 8, 1, 1);

  mtime_str = g_strdup_printf ("%ld", mtime);

  if (error)
    {
      gchar *code_str;
      const gchar *domain;

      if (error->domain == G_FILE_ERROR)
	domain = FILE_ERROR_NAME;
      else
	domain = PIXBUF_ERROR_NAME;

      code_str = g_strdup_printf ("%d", error->code);
      saved_ok = gdk_pixbuf_save (pixbuf, tmp_filename, "png", &err_ret,
				  THUMB_URI_KEY, uri,
				  THUMB_MTIME_KEY, mtime_str,
				  THUMB_SOFTWARE_KEY, THUMB_SOFTWARE_VALUE,
				  THUMB_ERROR_DOMAIN_KEY, domain,
				  THUMB_ERROR_CODE_KEY, code_str,
				  THUMB_ERROR_MESSAGE_KEY, error->message,
				  NULL);
      g_free (code_str);
    }
  else
    {
      saved_ok = gdk_pixbuf_save (pixbuf, tmp_filename, "png", &err_ret,
				  THUMB_URI_KEY, uri,
				  THUMB_MTIME_KEY, mtime_str,
				  THUMB_SOFTWARE_KEY, THUMB_SOFTWARE_VALUE,
				  NULL);
    }

  if (!saved_ok)
    {
      g_message ("Error saving fail thumbnail: %s", err_ret->message);
      g_error_free (err_ret);
    }
  else
    {
      chmod (tmp_filename, 0600);
      rename (tmp_filename, filename);
    }

  g_free (tmp_filename);
  g_free (filename);
  g_free (mtime_str);
}


/**
 * egg_pixbuf_get_thumbnail_for_pixbuf:
 * @pixbuf: the full-sized source pixbuf.
 * @size: the size of the thumbnailnail to generate.
 * @uri: the URI location of @pixbuf.
 * @mtime: the last-modified time of @uri.
 * 
 * Creates a thumbnail of the in-memory @pixbuf at @size, using @uri and
 * @mtime for the pre-requisite metadata.
 * 
 * Returns: a new thumbnail of @pixbuf which must be un-referenced with
 *  g_object_unref() when no longer needed, or %NULL.
 * 
 * Since: 2.6
 **/
GdkPixbuf *
egg_pixbuf_get_thumbnail_for_pixbuf (GdkPixbuf             *pixbuf,
				     const gchar           *uri,
				     time_t                 mtime,
				     EggPixbufThumbnailSize size)
{
  GdkPixbuf *retval;
  gint width, height;

  g_return_val_if_fail (GDK_IS_PIXBUF (pixbuf), NULL);
  g_return_val_if_fail (size == EGG_PIXBUF_THUMBNAIL_NORMAL ||
			size == EGG_PIXBUF_THUMBNAIL_LARGE, NULL);
  g_return_val_if_fail (uri != NULL && uri[0] != '\0', NULL);

  width = gdk_pixbuf_get_width (pixbuf);
  height = gdk_pixbuf_get_height (pixbuf);

  if (width > size || height > size)
    {
      gdouble scale;

      if (width > height)
	scale = (gdouble) size / width;
      else
	scale = (gdouble) size / height;

      retval = gdk_pixbuf_scale_simple (pixbuf, scale * width, scale *height,
					GDK_INTERP_BILINEAR);
    }
  else
    {
      retval = gdk_pixbuf_copy (pixbuf);
    }

  egg_pixbuf_set_thumbnail_uri (retval, uri);
  egg_pixbuf_set_thumbnail_mtime (retval, mtime);
  egg_pixbuf_set_thumbnail_size (retval, size);
  egg_pixbuf_set_thumbnail_description (retval,
					gdk_pixbuf_get_option (pixbuf,
							       THUMB_DESCRIPTION_KEY));

  return retval;
}

/* ******************* *
 *  Testing Functions  *
 * ******************* */

/**
 * egg_pixbuf_is_thumbnail:
 * @pixbuf: the pixbuf to test.
 * @uri: the source URI of pixbuf (or %NULL to ignore this test).
 * @mtime: the modification time of @uri (or %-1 to ignore this test).
 * 
 * This function will always check for thumbnail metadata attached to @pixbuf,
 * specifically the existance of a URI value. If @uri is non-%NULL, then the URI
 * value on @pixbuf will be compared with it. If @mtime is greater than or equal
 * to %0, then the modification time value will also be checked.
 * 
 * See also: egg_pixbuf_set_thumbnail_uri(), egg_pixbuf_set_thumbnail_mtime().
 * 
 * Returns: %TRUE if @pixbuf can be used as a thumbnail, %FALSE if it cannot.
 * 
 * Since: 2.6
 **/
gboolean
egg_pixbuf_is_thumbnail (GdkPixbuf   *pixbuf,
			 const gchar *uri,
			 time_t       mtime)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (pixbuf), FALSE);
  g_return_val_if_fail (uri == NULL || uri[0] != '\0', FALSE);

  data = get_thumbnail_data (pixbuf);

  /* Must have thumbnail data and matching URIs. */
  if (!data || !data->uri || (uri && strcmp (data->uri, uri) != 0))
    return FALSE;

  /* Thumbnails of local URIs must have matching mtime. */
  if (mtime >= 0 && uri && g_ascii_strncasecmp (data->uri, "file:", 5) == 0)
    {
      if (data->mtime != mtime)
	return FALSE;
    }
  /* Thumbnails of remote URIs expire after 30 days. We could require the user
     pass the proper mtime value for remote URIs, but why? */
  else if (mtime >= 0)
    {
      time_t current_time;

      current_time = time (NULL);

      if (data->mtime + EXPIRATION_TIME < current_time)
	return FALSE;
    }

  return TRUE;
}


/* ***************** *
 *  Getters/Setters  *
 * ***************** */

/**
 * egg_pixbuf_get_thumbnail_size:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the escaped URI that @thumbnail is a preview of.
 * 
 * Returns: a character array which should not be modified or freed.
 * 
 * Since: 2.6
 **/
EggPixbufThumbnailSize
egg_pixbuf_get_thumbnail_size (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail),
			EGG_PIXBUF_THUMBNAIL_UNKNOWN);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->size : EGG_PIXBUF_THUMBNAIL_UNKNOWN);
}

/**
 * egg_pixbuf_set_thumbnail_size:
 * @thumbnail: the thumbnail to modify.
 * @size: the size of @thumbnail.
 * 
 * Sets the size metadata for @thumbnail. This function may only be
 * called once for a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_size (GdkPixbuf             *thumbnail,
			       EggPixbufThumbnailSize size)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));
  g_return_if_fail (size == EGG_PIXBUF_THUMBNAIL_NORMAL ||
		    size == EGG_PIXBUF_THUMBNAIL_LARGE);

  data = ensure_thumbnail_data (thumbnail);
  data->size = size;
}

/**
 * egg_pixbuf_get_thumbnail_uri:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the escaped URI that @thumbnail is a preview of.
 * 
 * Returns: a character array which should not be modified or freed.
 * 
 * Since: 2.6
 **/
G_CONST_RETURN gchar *
egg_pixbuf_get_thumbnail_uri (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), NULL);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->uri : NULL);
}

/**
 * egg_pixbuf_set_thumbnail_uri:
 * @thumbnail: the thumbnail to modify.
 * @uri: the escaped URI that @thumbnail is a preview of.
 * 
 * Sets the URI metadata for @thumbnail. This function may only be
 * called once for a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_uri (GdkPixbuf   *thumbnail,
			      const gchar *uri)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));
  g_return_if_fail (uri != NULL && uri[0] != '\0');

  data = ensure_thumbnail_data (thumbnail);
  g_free (data->uri);
  data->uri = g_strdup (uri);
}

/**
 * egg_pixbuf_get_thumbnail_mime_type:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the mime-type of the file that @thumbnail is a preview of.
 * 
 * Returns: a character array which should not be modified or freed.
 * 
 * Since: 2.6
 **/
G_CONST_RETURN gchar *
egg_pixbuf_get_thumbnail_mime_type (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), NULL);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->mime_type : NULL);
}

/**
 * egg_pixbuf_set_thumbnail_mime_type:
 * @thumbnail: the thumbnail to modify.
 * @mime_type: the mime type of the file that @thumbnail is a preview of.
 * 
 * Sets the @mime_type metadata for @thumbnail. This function may only be called
 * once on a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_mime_type (GdkPixbuf   *thumbnail,
				    const gchar *mime_type)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));
  g_return_if_fail (mime_type != NULL && mime_type[0] != '\0');

  data = ensure_thumbnail_data (thumbnail);
  g_free (data->mime_type);
  data->mime_type = g_strdup (mime_type);
}

/**
 * egg_pixbuf_get_thumbnail_description:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the user-specified description (comment) for the file that
 * @thumbnail is a preview of. If this metadata was not saved (or does not
 * exist for @thumbnail), NULL will be returned.
 * 
 * Returns: a character array which should not be modified or freed.
 * 
 * Since: 2.6
 **/
G_CONST_RETURN gchar *
egg_pixbuf_get_thumbnail_description (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), NULL);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->description : NULL);
}

/**
 * egg_pixbuf_set_thumbnail_description:
 * @thumbnail: the thumbnail to modify.
 * @description: the description of the file that @thumbnail is a preview of.
 * 
 * Sets the user-specified @description metadata for @thumbnail. This function
 * may only be called once on a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_description (GdkPixbuf   *thumbnail,
				      const gchar *description)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));
  g_return_if_fail (description != NULL && description[0] != '\0');

  data = ensure_thumbnail_data (thumbnail);
  g_free (data->description);
  data->description = g_strdup (description);
}

/**
 * egg_pixbuf_get_thumbnail_mtime:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the UNIX time (seconds since the epoch/time_t) the file which
 * @thumbnail is a preview of was modified on when the @thumbnail was created.
 * If this metadata was not saved with @thumbnail, %-1 will be returned.
 * 
 * Returns: a UNIX seconds-since-epoch time value, or %-1.
 * 
 * Since: 2.6
 **/
time_t
egg_pixbuf_get_thumbnail_mtime (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), -1);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->mtime : -1);
}

/**
 * egg_pixbuf_set_thumbnail_mtime:
 * @thumbnail: the thumbnail to modify.
 * @mtime: the last-modified time of the file that @thumbnail is a preview of.
 * 
 * Sets the last-modified @mtime metadata for @thumbnail. This function
 * may only be called once on a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_mtime (GdkPixbuf *thumbnail,
				time_t     mtime)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));

  data = ensure_thumbnail_data (thumbnail);
  data->mtime = mtime;
}

/**
 * egg_pixbuf_get_thumbnail_filesize:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the size in bytes of the file which @thumbnail is a preview of. If
 * this metadata was not saved with @thumbnail, %-1 will be returned.
 * 
 * Returns: a 64-bit integer.
 * 
 * Since: 2.6
 **/
gssize
egg_pixbuf_get_thumbnail_filesize (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), -1);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->filesize : -1);
}

/**
 * egg_pixbuf_set_thumbnail_filesize:
 * @thumbnail: the thumbnail to modify.
 * @filesize: the size (in bytes) of the file that @thumbnail is a preview of.
 * 
 * Sets the @filesize metadata for @thumbnail. This function may only be called
 * once on a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_filesize (GdkPixbuf *thumbnail,
				   gssize     filesize)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));

  data = ensure_thumbnail_data (thumbnail);
  data->filesize = filesize;
}

/**
 * egg_pixbuf_get_thumbnail_image_width:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the width (in pixels) of the image contained in the file that
 * @thumbnail is a preview of. If this metadata was not saved with @thumbnail
 * (e.g. if the original file was not an image), %-1 will be returned.
 * 
 * Returns: an integer.
 * 
 * Since: 2.6
 **/
gint
egg_pixbuf_get_thumbnail_image_width (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), -1);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->image_width : -1);
}

/**
 * egg_pixbuf_set_thumbnail_image_width:
 * @thumbnail: the thumbnail to modify.
 * @image_width: the width (in pixels) of the image file that @thumbnail is a preview of.
 * 
 * Sets the @image_width metadata for @thumbnail. This function may only be
 * called once on a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_image_width (GdkPixbuf *thumbnail,
				      gint       image_width)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));

  data = ensure_thumbnail_data (thumbnail);
  data->image_width = image_width;
}

/**
 * egg_pixbuf_get_thumbnail_image_height:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the height (in pixels) of the image contained in the file that
 * @thumbnail is a preview of. If this metadata was not saved with @thumbnail
 * (e.g. if the original file was not an image), %-1 will be returned.
 * 
 * Returns: an integer.
 * 
 * Since: 2.6
 **/
gint
egg_pixbuf_get_thumbnail_image_height (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), -1);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->image_height : -1);
}

/**
 * egg_pixbuf_set_thumbnail_image_height:
 * @thumbnail: the thumbnail to modify.
 * @image_height: the height (in pixels) of the image file that @thumbnail is a preview of.
 * 
 * Sets the @image_height metadata for @thumbnail. This function may only be
 * called once on a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_image_height (GdkPixbuf *thumbnail,
				       gint       image_height)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));

  data = ensure_thumbnail_data (thumbnail);
  data->image_height = image_height;
}

/**
 * egg_pixbuf_get_thumbnail_document_pages:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the number of pages in the document contained in the file that
 * @thumbnail is a preview of. If this metadata was not saved with @thumbnail
 * (e.g. if the original file was not a paged document), %-1 will be returned.
 * 
 * Returns: an integer.
 * 
 * Since: 2.6
 **/
gint
egg_pixbuf_get_thumbnail_document_pages (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), -1);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->document_pages : -1);
}

/**
 * egg_pixbuf_set_thumbnail_document_pages:
 * @thumbnail: the thumbnail to modify.
 * @document_pages: the number of pages in the document file that @thumbnail is
 *   a preview of.
 * 
 * Sets the @document_pages metadata for @thumbnail. This function may only be
 * called once on a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_document_pages (GdkPixbuf *thumbnail,
					 gint       document_pages)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));

  data = ensure_thumbnail_data (thumbnail);
  data->document_pages = document_pages;
}

/**
 * egg_pixbuf_get_thumbnail_movie_length:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the length (in seconds) of the movie contained in the file that
 * @thumbnail is a preview of. If this metadata was not saved with @thumbnail
 * (e.g. if the original file was not a movie), %-1 will be returned.
 * 
 * Returns: a 64-bit integer.
 * 
 * Since: 2.6
 **/
time_t
egg_pixbuf_get_thumbnail_movie_length (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), -1);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->movie_length : -1);
}

/**
 * egg_pixbuf_set_thumbnail_movie_length:
 * @thumbnail: the thumbnail to modify.
 * @movie_length: the length (in seconds) of the movie file that @thumbnail is a preview of.
 * 
 * Sets the @movie_length metadata for @thumbnail. This function may only be
 * called once on a particular pixbuf.
 * 
 * Since: 2.6
 **/
void
egg_pixbuf_set_thumbnail_movie_length (GdkPixbuf *thumbnail,
				       time_t     movie_length)
{
  ThumbnailData *data;

  g_return_if_fail (GDK_IS_PIXBUF (thumbnail));

  data = ensure_thumbnail_data (thumbnail);
  data->movie_length = movie_length;
}

/**
 * egg_pixbuf_get_thumbnail_software:
 * @thumbnail: the thumbnail to examine.
 * 
 * Retreives the name of the software which originally created @thumbnail. If
 * this metadata was not saved (or does not exist for @thumbnail), NULL will be
 * returned.
 * 
 * Returns: a character array which should not be modified or freed.
 * 
 * Since: 2.6
 **/
G_CONST_RETURN gchar *
egg_pixbuf_get_thumbnail_software (GdkPixbuf *thumbnail)
{
  ThumbnailData *data;

  g_return_val_if_fail (GDK_IS_PIXBUF (thumbnail), NULL);

  data = get_thumbnail_data (thumbnail);

  return (data ? data->software : NULL);
}


/* ******************** *
 *  Filename Functions  *
 * ******************** */

/**
 * egg_pixbuf_get_thumbnail_filename:
 * @uri: the URI of the file to thumbnail.
 * @size: the desired size of the thumbnail.
 * 
 * Constructs the global thumbnail filename for @uri at @size. This filename
 * can be used to open and save the thumbnail.
 * 
 * Returns: a newly-allocated character array which should be freed with
 *  g_free() when no longer needed.
 *
 * Since: 2.6
 **/
gchar *
egg_pixbuf_get_thumbnail_filename (const gchar           *uri,
				   EggPixbufThumbnailSize size)
{
  const gchar *home_dir = NULL;
  gchar *md5, *basename, *filename;

  g_return_val_if_fail (uri != NULL && uri[0] != '\0', NULL);
  g_return_val_if_fail (size == EGG_PIXBUF_THUMBNAIL_NORMAL ||
			size == EGG_PIXBUF_THUMBNAIL_LARGE, FALSE);

  if (home_dir == NULL)
    home_dir = g_get_home_dir ();
  else
    home_dir = g_get_tmp_dir ();

#ifdef LIBAWN_USE_XFCE
  md5 = exo_str_get_md5_str (uri);
#else
  md5 = g_compute_checksum_for_string (G_CHECKSUM_MD5, uri, strlen (uri));
#endif
  basename = g_strconcat (md5, ".png", NULL);
  filename = g_build_filename (home_dir, ".thumbnails", SIZE_TO_DIR (size),
			       basename, NULL);
  g_free (md5);
  g_free (basename);

  return filename;
}

#if 0

/**
 * egg_pixbuf_get_local_thumbnail_uri:
 * @uri: the URI of the file to thumbnail.
 * @size: the desired size of the thumbnail.
 * 
 * Constructs the correct thumbnail URI for the "local" thumbnail directory,
 * intended for removable media.
 * 
 * Returns: a string URI which must be freed with g_free() when no longer
 *  needed, or %NULL.
 * 
 * Since: 2.6
 **/
gchar *
egg_pixbuf_get_local_thumbnail_uri (const gchar           *uri,
				    EggPixbufThumbnailSize size)
{
  gchar *retval;

  g_return_val_if_fail (uri != NULL && uri[0] != '\0', NULL);
  g_return_val_if_fail (size == EGG_PIXBUF_THUMBNAIL_NORMAL ||
			size == EGG_PIXBUF_THUMBNAIL_LARGE, FALSE);

  retval = NULL;

  return retval;
}

#endif /* Disabled */
