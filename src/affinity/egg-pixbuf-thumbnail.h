/* Egg Libraries: egg-pixbuf-thumbnail.h
 * 
 * Copyright (c) 2004 James M. Cape <jcape@ignore-your.tv>
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

#ifndef __EGG_PIXBUF_THUMBNAIL_H__
#define __EGG_PIXBUF_THUMBNAIL_H__ 1

#include <time.h>
#include <gdk-pixbuf/gdk-pixbuf.h>

G_BEGIN_DECLS


typedef enum /* <prefix=EGG_PIXBUF_THUMBNAIL> */
{
  EGG_PIXBUF_THUMBNAIL_UNKNOWN = -1,
  EGG_PIXBUF_THUMBNAIL_NORMAL  = 128,
  EGG_PIXBUF_THUMBNAIL_LARGE   = 256
}
EggPixbufThumbnailSize;


GdkPixbuf             *egg_pixbuf_get_thumbnail_for_file         (const gchar           *filename,
								  EggPixbufThumbnailSize size,
								  GError               **error);
GdkPixbuf             *egg_pixbuf_get_thumbnail_for_file_at_size (const gchar           *filename,
								  gint                   pixel_size,
								  GError               **error);

GdkPixbuf             *egg_pixbuf_get_thumbnail_for_pixbuf       (GdkPixbuf             *pixbuf,
								  const gchar           *uri,
								  time_t                 mtime,
								  EggPixbufThumbnailSize size);

GdkPixbuf             *egg_pixbuf_load_thumbnail                 (const gchar           *uri,
								  time_t                 mtime,
								  EggPixbufThumbnailSize size);
GdkPixbuf             *egg_pixbuf_load_thumbnail_at_size         (const gchar           *uri,
								  time_t                 mtime,
								  gint                   pixel_size);

gboolean               egg_pixbuf_save_thumbnail                 (GdkPixbuf             *thumbnail,
								  GError               **error,
								  ...);
gboolean               egg_pixbuf_save_thumbnailv                (GdkPixbuf             *thumbnail,
								  gchar                **keys,
								  gchar                **values,
								  GError               **error);

gboolean               egg_pixbuf_has_failed_thumbnail           (const gchar           *uri,
								  time_t                 mtime,
								  GError               **error);
void                   egg_pixbuf_save_failed_thumbnail          (const gchar           *uri,
								  time_t                 mtime,
								  const GError          *error);

gboolean               egg_pixbuf_is_thumbnail                   (GdkPixbuf             *pixbuf,
								  const gchar           *uri,
								  time_t                 mtime);
								  

EggPixbufThumbnailSize egg_pixbuf_get_thumbnail_size             (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_size             (GdkPixbuf             *thumbnail,
								  EggPixbufThumbnailSize size);

G_CONST_RETURN gchar  *egg_pixbuf_get_thumbnail_uri              (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_uri              (GdkPixbuf             *thumbnail,
								  const gchar           *uri);
G_CONST_RETURN gchar  *egg_pixbuf_get_thumbnail_mime_type        (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_mime_type        (GdkPixbuf             *thumbnail,
								  const gchar           *mime_type);
G_CONST_RETURN gchar  *egg_pixbuf_get_thumbnail_description      (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_description      (GdkPixbuf             *thumbnail,
								  const gchar           *description);
time_t		       egg_pixbuf_get_thumbnail_mtime            (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_mtime            (GdkPixbuf             *thumbnail,
								  time_t                 mtime);
gssize		       egg_pixbuf_get_thumbnail_filesize         (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_filesize         (GdkPixbuf             *thumbnail,
								  gssize                 filesize);
gint		       egg_pixbuf_get_thumbnail_image_width      (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_image_width      (GdkPixbuf             *thumbnail,
								  gint                   image_width);
gint		       egg_pixbuf_get_thumbnail_image_height     (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_image_height     (GdkPixbuf             *thumbnail,
								  gint                   image_height);
gint		       egg_pixbuf_get_thumbnail_document_pages   (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_document_pages   (GdkPixbuf             *thumbnail,
								  gint                    document_pages);
time_t		       egg_pixbuf_get_thumbnail_movie_length     (GdkPixbuf             *thumbnail);
void                   egg_pixbuf_set_thumbnail_movie_length     (GdkPixbuf             *thumbnail,
								  time_t                 movie_length);

G_CONST_RETURN gchar  *egg_pixbuf_get_thumbnail_software         (GdkPixbuf             *thumbnail);

gchar                 *egg_pixbuf_get_thumbnail_filename         (const gchar           *uri,
								  EggPixbufThumbnailSize size);
/* gchar                 *egg_pixbuf_get_local_thumbnail_uri        (const gchar           *uri,
								  EggPixbufThumbnailSize size); */

G_END_DECLS

#endif /* !__EGG_PIXBUF_THUMBNAIL_H__ */
