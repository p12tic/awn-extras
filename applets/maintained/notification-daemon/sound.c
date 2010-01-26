/*
 * sound.c - Sound support portion of the destop notification spec
 *
 * Copyright (C) 2007 Jim Ramsay <i.am@jimramsay.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 */
#include "config.h"

#include "sound.h"

#ifdef HAVE_GSTREAMER
#include <gst/gst.h>

static GstElement *player;

static void
sound_play_uri(const gchar* uri)
{
  if (player == NULL)
    return;
  /*
   * TODO: Fade out the current sound and then start the new sound?
   *       Right now we just cut off the existing sound, which is kind of
   *       abrupt
   */

  /* Stop the pipeline */
  gst_element_set_state(player, GST_STATE_NULL);

  /* Set the input to a local file uri */
  g_object_set(G_OBJECT(player), "uri", uri, NULL);

  /* Start the pipeline again */
  gst_element_set_state(player, GST_STATE_PLAYING);
}

#endif /* HAVE_GSTREAMER */

void
sound_init(void)
{
#ifdef HAVE_GSTREAMER
  gst_init(NULL, NULL);

  player = gst_element_factory_make("playbin", "Notification Player");

  if (player != NULL)
  {
    /*
     * Instead of using the default audiosink, use the gconfaudiosink,
     * which will respect the defaults in gstreamer-properties
     */
    g_object_set(G_OBJECT(player), "audio-sink",
                 gst_element_factory_make("gconfaudiosink", "GconfAudioSink"),
                 NULL);
  }

#endif /* HAVE_GSTREAMER */
}

void
sound_play(const gchar* filename)
{
  /* We are guaranteed here that the file exists */
#ifdef HAVE_GSTREAMER
  /* gstreamer's playbin takes uris, so make a file:// uri */
  gchar* uri = g_strdup_printf("file://%s", filename);
  sound_play_uri(uri);
  g_free(uri);
#endif /* HAVE_GSTREAMER */
}

