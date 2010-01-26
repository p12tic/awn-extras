/*
 * Copyright (C) 2007, 2008 Rodney Cryderman <rcryderman@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
*/


#ifndef __MENU_LIST_ITEM_
#define __MENU_LIST_ITEM_
#include <gtk/gtk.h>
#include <glib.h>
#include "menu.h"


enum
{
  MENU_ITEM_INVALID = 0,
  MENU_ITEM_DIRECTORY,
  MENU_ITEM_ENTRY,
  MENU_ITEM_SEPARATOR,
  MENU_ITEM_HEADER,
  MENU_ITEM_ALIAS,

  MENU_ITEM_SEARCH,
  MENU_ITEM_RUN,
  MENU_ITEM_BLANK,
  MENU_ITEM_DRIVE
};

typedef struct
{
  int   item_type;
  gchar  * name;
  gchar  * icon;
  union
  {
    gchar  * exec;
    gchar * mount_point;
  };
  gchar  * comment;
  gchar  * desktop;
  gboolean launch_in_terminal;
  gpointer parent_menu;
  GtkWidget *widget;
  GtkWidget *normal;
  GtkWidget *hover;
  GtkWidget *click;
  gpointer  *drive;
  union
  {
    GSList   *sublist;

  };
  union
  {
    GtkWidget *text_entry;
    GtkWidget *search_entry;
    GtkWidget *run_entry;
    void (*monitor)(gpointer callback, gpointer data, gpointer box);
    gboolean(*drive_prep)(gpointer menu_item, gchar * filemanager);
    gboolean(*drive_mount)(gpointer menu_item, gchar * filemanager);
    gpointer null;

  } ;
}Menu_list_item;


#endif
