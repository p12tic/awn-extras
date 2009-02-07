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


#define GMENU_I_KNOW_THIS_IS_UNSTABLE

#include <libgnomevfs/gnome-vfs.h>
#include <libgnomevfs/gnome-vfs-utils.h>
#include <gnome-menus/gmenu-tree.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>

#include <libawn-extras/awn-extras.h>

#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <string.h>
#include <glib.h>
#include <assert.h>
#include <libgen.h>
#include <ctype.h>
#include <libnotify/notify.h>
#include <glib/gstdio.h>

#include "menu_list_item.h"


char * G_file_manager;


static gchar *_G_mount_result_filemanager = NULL;

typedef struct
{
  Menu_list_item ** data;
  void(* callback)(gpointer, gpointer);
  GtkWidget * box;

}Monitor_places;

Monitor_places  * Monitor_place = NULL;



static void print_directory(GMenuTreeDirectory *directory);
static void print_entry(GMenuTreeEntry *entry, const char *path);
static char *make_path(GMenuTreeDirectory *directory);
static void append_directory_path(GMenuTreeDirectory *directory, GString *path);
static void update_places(Menu_list_item **p, char* file_manager);
static Menu_list_item *get_separator(void);
static void _do_update_places(Monitor_places * user_data);
static Menu_list_item *get_blank(void);

static void
append_directory_path(GMenuTreeDirectory *directory,
                      GString            *path)
{
  GMenuTreeDirectory *parent;

  parent = gmenu_tree_item_get_parent(GMENU_TREE_ITEM(directory));

  if (!parent)
  {
    g_string_append_c(path, '/');
    return;
  }

  append_directory_path(parent, path);

  g_string_append(path, gmenu_tree_directory_get_name(directory));
  g_string_append_c(path, '/');

  gmenu_tree_item_unref(parent);
}

static char *
make_path(GMenuTreeDirectory *directory)
{
  GString *path;

  g_return_val_if_fail(directory != NULL, NULL);

  path = g_string_new(NULL);

  append_directory_path(directory, path);

  return g_string_free(path, FALSE);
}

static void
print_entry(GMenuTreeEntry *entry,
            const char     *path)
{
  char *utf8_path;
  char *utf8_file_id;

  utf8_path = g_filename_to_utf8(gmenu_tree_entry_get_desktop_file_path(entry),
                                 -1, NULL, NULL, NULL);

  utf8_file_id = g_filename_to_utf8(gmenu_tree_entry_get_desktop_file_id(entry),
                                    -1, NULL, NULL, NULL);

  g_print("%s\t%s\t%s%s\n",
          path,
          utf8_file_id ? utf8_file_id : _("Invalid desktop file ID"),
          utf8_path ? utf8_path : _("[Invalid Filename]"),
          gmenu_tree_entry_get_is_excluded(entry) ? _(" <excluded>") : "");

  g_free(utf8_file_id);
  g_free(utf8_path);
}

static void
print_directory(GMenuTreeDirectory *directory)
{
  GSList     *items;
  GSList     *tmp;
  const char *path;
  char       *freeme;

  freeme = make_path(directory);

  if (!strcmp(freeme, "/"))
    path = freeme;
  else
    path = freeme + 1;

  items = gmenu_tree_directory_get_contents(directory);

  tmp = items;

  while (tmp != NULL)
  {
    GMenuTreeItem *item = tmp->data;

    switch (gmenu_tree_item_get_type(item))
    {

      case GMENU_TREE_ITEM_ENTRY:
        print_entry(GMENU_TREE_ENTRY(item), path);
        break;

      case GMENU_TREE_ITEM_DIRECTORY:
        print_directory(GMENU_TREE_DIRECTORY(item));
        break;

      case GMENU_TREE_ITEM_HEADER:

      case GMENU_TREE_ITEM_SEPARATOR:
        break;

      case GMENU_TREE_ITEM_ALIAS:
      {
        GMenuTreeItem *aliased_item;

        aliased_item = gmenu_tree_alias_get_item(GMENU_TREE_ALIAS(item));

        if (gmenu_tree_item_get_type(aliased_item) == GMENU_TREE_ITEM_ENTRY)
          print_entry(GMENU_TREE_ENTRY(aliased_item), path);
      }

      break;

      default:
        g_assert_not_reached();
        break;
    }

    gmenu_tree_item_unref(tmp->data);

    tmp = tmp->next;
  }

  g_slist_free(items);

  g_free(freeme);
}

static void
add_entry(GMenuTreeEntry *entry,
          const char     *path, GSList**p)
{
  GSList*  data = *p;
  char *utf8_path;
  char *utf8_file_id;
  Menu_list_item * item;
  gchar * file_name;

  utf8_path = g_filename_to_utf8(gmenu_tree_entry_get_desktop_file_path(entry),
                                 -1, NULL, NULL, NULL);

  utf8_file_id = g_filename_to_utf8(gmenu_tree_entry_get_desktop_file_id(entry),
                                    -1, NULL, NULL, NULL);
  file_name = utf8_path ? utf8_path : _("[Invalid Filename]");
  item = g_malloc(sizeof(Menu_list_item));
  item->item_type = MENU_ITEM_ENTRY;
  item->name = gmenu_tree_entry_get_name(entry);
  item->icon = gmenu_tree_entry_get_icon(entry);
  item->exec = gmenu_tree_entry_get_exec(entry);
  char *str = item->exec;

  while (*str)
  {
    if (*str == '%')
    {
      *str = ' ';

      if (*(str + 1))
      {
        str++;
        *str = ' ';
      }
    }

    str++;
  }

  item->comment = gmenu_tree_entry_get_comment(entry);

  item->launch_in_terminal = gmenu_tree_entry_get_launch_in_terminal(entry);
  item->desktop = g_strdup(file_name);
  data = g_slist_append(data, item);
  *p = data;

  g_free(utf8_file_id);
  g_free(utf8_path);
}


static void
fill_er_up(GMenuTreeDirectory *directory, GSList**p)
{
  GSList*  data = *p;
  GSList     *items;
  GSList     *tmp;
  const char *path;
  char       *freeme;

  freeme = make_path(directory);

  if (!strcmp(freeme, "/"))
    path = freeme;
  else
    path = freeme + 1;

  items = gmenu_tree_directory_get_contents(directory);

  tmp = items;

  while (tmp != NULL)
  {
    GMenuTreeItem *item = tmp->data;

    switch (gmenu_tree_item_get_type(item))
    {

      case GMENU_TREE_ITEM_ENTRY:
        // print_entry (GMENU_TREE_ENTRY (item), path);
        add_entry(GMENU_TREE_ENTRY(item), path, &data);
        break;

      case GMENU_TREE_ITEM_DIRECTORY:
      {
        Menu_list_item * dir_item;
        dir_item = g_malloc(sizeof(Menu_list_item));
        dir_item->item_type = MENU_ITEM_DIRECTORY;
        dir_item->name = gmenu_tree_directory_get_name(item);
        dir_item->desktop = gmenu_tree_directory_get_desktop_file_path(item);
        dir_item->comment = NULL;
        dir_item->null = NULL;
        dir_item->comment = gmenu_tree_directory_get_comment(item);
        dir_item->icon = gmenu_tree_directory_get_icon(item);
        dir_item->sublist = NULL;
        data = g_slist_append(data, dir_item);
        fill_er_up(GMENU_TREE_DIRECTORY(item), &dir_item->sublist);
        dir_item->sublist = g_slist_prepend(dir_item->sublist, get_blank());
        dir_item->sublist = g_slist_append(dir_item->sublist, get_blank());
      }

      break;

      case GMENU_TREE_ITEM_HEADER:
//    printf("GMENU_TREE_ITEM_HEADER\n");
        break;

      case GMENU_TREE_ITEM_SEPARATOR:
//    printf("GMENU_TREE_ITEM_HEADER\n");
        break;

      case GMENU_TREE_ITEM_ALIAS:
//    printf("GMENU_TREE_ITEM_ALIAS\n");
        /*      {
             GMenuTreeItem *aliased_item;

             aliased_item = gmenu_tree_alias_get_item (GMENU_TREE_ALIAS (item));
             if (gmenu_tree_item_get_type (aliased_item) == GMENU_TREE_ITEM_ENTRY)
                print_entry (GMENU_TREE_ENTRY (aliased_item), path);
              }*/
        break;

      default:
        g_assert_not_reached();
        break;
    }

    gmenu_tree_item_unref(tmp->data);

    tmp = tmp->next;
  }

  g_slist_free(items);

  g_free(freeme);
  *p = data;
}








void _mount_result(gboolean succeeded, char *error, char *detailed_error, char* comment)
{
  gchar * mess;

  if (!succeeded)
  {
    mess = g_strdup_printf("Mount Failed\n%s\nError:  %s\n", comment, detailed_error);
    display_message("Cairo Menu", mess, 0);
    g_free(mess);
  }

  g_free(comment);
}

gboolean _mount_connected(Menu_list_item * p, char * filemanager)
{

  char * cmd;
  char * mess;
  _G_mount_result_filemanager = filemanager;

  mess = g_strdup_printf("%s is not mounted. \nAttempting to mount", p->name);
  display_message("Cairo Menu", mess, 4000);
  gnome_vfs_drive_mount(p->drive, _mount_result, g_strdup(p->comment));
  g_free(mess);
  return FALSE;
}

void _unmount_result(gboolean succeeded, char *error, char *detailed_error, char* comment)
{
  gchar * mess;

  if (!succeeded)
  {
    mess = g_strdup_printf("Unmount Failed\n%s\nError:  %s\n", comment, detailed_error);
    display_message("Cairo Menu", mess, 0);
    g_free(mess);
  }

  g_free(comment);
}

void _eject_result(gboolean succeeded, char *error, char *detailed_error, char* comment)
{
  gchar * mess;

  if (!succeeded)
  {
    mess = g_strdup_printf("Eject Failed\n%s\nError:  %s\n", comment, detailed_error);
    display_message("Cairo Menu", mess, 0);
    g_free(mess);
  }

  g_free(comment);
}


gboolean _do_update_places_wrapper(Monitor_places * p)
{
  _do_update_places(p);
  return FALSE;
}

void backend_unmount(Menu_list_item * menu_item)
{
  gnome_vfs_drive_unmount(menu_item->drive, _unmount_result, g_strdup(menu_item->comment));
}

void backend_eject(Menu_list_item * menu_item)
{
  gnome_vfs_drive_eject(menu_item->drive, _eject_result, g_strdup(menu_item->comment));
}

void _vfs_changed_v_u(GnomeVFSDrive  *drive, GnomeVFSVolume *volume, gpointer null)
{
  g_timeout_add(500, _do_update_places_wrapper, Monitor_place);
}

void _vfs_changed_v_m(GnomeVFSDrive  *drive, GnomeVFSVolume *volume, gpointer null)
{
  g_timeout_add(500, _do_update_places_wrapper, Monitor_place);
}

void _vfs_changed_d_d(GnomeVFSDrive  *drive, GnomeVFSVolume *volume, gpointer null)
{
  _do_update_places(Monitor_place);
}

void _vfs_changed_d_c(GnomeVFSDrive  *drive, GnomeVFSVolume *volume, gpointer null)
{
  _do_update_places(Monitor_place);
}

void _fillin_connected(GnomeVFSDrive * drive, GSList ** p)
{

// printf("drive=%s\n",gnome_vfs_drive_get_display_name(drive));
  Menu_list_item * item;
  GSList *sublist = *p;
  char * dev_path;

  item = g_malloc(sizeof(Menu_list_item));

  item->item_type = MENU_ITEM_DRIVE;
  item->name = g_strdup(gnome_vfs_drive_get_display_name(drive));
  item->icon = g_strdup(gnome_vfs_drive_get_icon(drive));
  item->drive = drive;
  // FIXME gnome_vfs_drive_get_mounted_volume is deprecated.



  if (gnome_vfs_drive_get_mounted_volume(drive))
  {

    GnomeVFSVolume* volume;
    volume = gnome_vfs_drive_get_mounted_volume(drive);
    item->mount_point = gnome_vfs_volume_get_activation_uri(volume);
    item->drive_prep = NULL;
    gnome_vfs_volume_unref(volume) ;
  }
  else
  {
    item->mount_point = g_strdup("Unmounted");
    item->drive_prep = _mount_connected;
  }

  dev_path = gnome_vfs_drive_get_device_path(drive);

  item->comment = g_strdup_printf("%s\n%s\n%s", item->name, item->mount_point, dev_path) ;
  item->desktop = g_strdup("");
  sublist = g_slist_append(sublist, item);
  g_free(dev_path);

  *p = sublist;
}


static Menu_list_item *get_separator(void)
{
  Menu_list_item * item;
  item = g_malloc(sizeof(Menu_list_item));
  item->item_type = MENU_ITEM_SEPARATOR;
  item->exec = NULL;
  item->name = NULL;
  item->icon = NULL;
  item->comment = NULL;
  item->sublist = NULL;
  item->null = NULL;
  item->widget = NULL;
  item->hover = NULL;
  item->normal = NULL;
  return item;
}

static Menu_list_item *get_blank(void)
{
  Menu_list_item * item;
  item = g_malloc(sizeof(Menu_list_item));
  item->item_type = MENU_ITEM_BLANK;
  item->exec = NULL;
  item->name = NULL;
  item->icon = NULL;
  item->comment = NULL;
  item->sublist = NULL;
  item->null = NULL;
  item->widget = NULL;
  item->hover = NULL;
  item->normal = NULL;
  return item;
}

static void update_places(Menu_list_item **p, char* file_manager)
{
  static GnomeVFSVolumeMonitor* vfsvolumes = NULL;
  Menu_list_item * sublist = *p;
  Menu_list_item * item;


  sublist = g_slist_append(sublist, get_blank());


  item = g_malloc(sizeof(Menu_list_item));
  item->item_type = MENU_ITEM_ENTRY;
  item->name = g_strdup("Home");
  item->icon = g_strdup("stock_home");
  const char *homedir = g_getenv("HOME");

  if (!homedir)
    homedir = g_get_home_dir();

  item->exec = g_strdup_printf("%s %s", file_manager, homedir);

  item->comment = g_strdup("Your Home Directory");

  item->desktop = g_strdup("");

  sublist = g_slist_append(sublist, item);

  item = g_malloc(sizeof(Menu_list_item));

  item->item_type = MENU_ITEM_ENTRY;

  item->name = g_strdup("File System");

  item->icon = g_strdup("stock_folder");

  item->exec = g_strdup_printf("%s /", file_manager);

  item->comment = g_strdup("Root File System");

  item->desktop = g_strdup("");

  sublist = g_slist_append(sublist, item);

//mount monitor
  if (!vfsvolumes)
  {
    vfsvolumes = gnome_vfs_get_volume_monitor();
    g_signal_connect(G_OBJECT(vfsvolumes), "volume-mounted", G_CALLBACK(_vfs_changed_v_m), NULL);
    g_signal_connect(G_OBJECT(vfsvolumes), "volume-unmounted", G_CALLBACK(_vfs_changed_v_u), NULL);
    g_signal_connect(G_OBJECT(vfsvolumes), "drive-disconnected" , G_CALLBACK(_vfs_changed_d_d), NULL);
    g_signal_connect(G_OBJECT(vfsvolumes), "drive-connected", G_CALLBACK(_vfs_changed_d_c), NULL);
  }

  GList *connected = gnome_vfs_volume_monitor_get_connected_drives(vfsvolumes);

  if (connected)
    g_list_foreach(connected, _fillin_connected, &sublist);

  g_list_free(connected);


  sublist = g_slist_append(sublist, get_separator());

/*bookmarks*/
  FILE* handle;

  gchar *  filename = g_strdup_printf("%s/.gtk-bookmarks", homedir);

  handle = g_fopen(filename, "r");

  if (handle)
  {
    char * line = NULL;
    size_t  len = 0;

    while (getline(&line, &len, handle) != -1)
    {
      gchar ** tokens;
      tokens = g_strsplit(line, " ", 2);

      if (tokens)
      {
        if (tokens[0])
        {
          gchar * shell_quoted;
          g_strstrip(tokens[0]);
          item = g_malloc(sizeof(Menu_list_item));
          item->item_type = MENU_ITEM_ENTRY;

          if (tokens[1])
          {
            g_strstrip(tokens[1]);
            item->name = g_strdup(tokens[1]);
          }
          else
          {
            item->name = urldecode(g_path_get_basename(tokens[0]), NULL);
          }

          item->icon = g_strdup("stock_folder");

          shell_quoted = g_shell_quote(tokens[0]);
          item->exec = g_strdup_printf("%s %s", file_manager, shell_quoted);
          g_free(shell_quoted);
          item->comment = g_strdup(tokens[0]);
          item->desktop = g_strdup("");
          sublist = g_slist_append(sublist, item);

        }

      }

      g_strfreev(tokens);

      free(line);

      line = NULL;
    }

    fclose(handle);

    g_free(filename);
  }
  else
  {
    printf("Unable to open bookmark file: %s/.gtk-bookmarks\n", homedir);
  }
  sublist = g_slist_append(sublist, get_blank());

  *p = sublist;
}

void free_menu_list_item(Menu_list_item * item, gpointer null)
{
  /* if (item->item_type==MENU_ITEM_DRIVE)
   {
    gnome_vfs_drive_unref(item->drive);
   }*/
  if (item->name)
    g_free(item->name);

  if (item->icon)
    g_free(item->icon);

  if (item->exec)
    g_free(item->exec);

  if (item->comment)
    g_free(item->comment);

// g_free(item->desktop);
// gboolean launch_in_terminal;
// void  * parent_menu;
// GSList  *sublist;
  if (item->widget)
    gtk_widget_destroy(item->widget);

  if (item->normal)
    gtk_widget_destroy(item->normal);

  if (item->hover)
    gtk_widget_destroy(item->hover);

  item->name = NULL;

  item->icon = NULL;

  item->exec = NULL;

  item->comment = NULL;

  item->widget = NULL;

  item->hover = NULL;

  item->normal = NULL;

// gtk_widget_destroy(item->click);

}


static void _do_update_places(Monitor_places * user_data)
{
  g_slist_foreach(*(user_data->data), free_menu_list_item, NULL);
  g_slist_free(*(user_data->data));
  *(user_data->data) = NULL;
  update_places(user_data->data, G_file_manager); //FIXME
  user_data->callback(user_data->data, user_data->box);
}


static void monitor_places_callback(GnomeVFSMonitorHandle *handle,
                                    const gchar *monitor_uri,
                                    const gchar *info_uri,
                                    GnomeVFSMonitorEventType event_type,
                                    Monitor_places * user_data)
{
// gtk_widget_destroy(user_data->box);
  _do_update_places(user_data);
}



static void monitor_places(gpointer callback, gpointer data, gpointer box)
{
  GnomeVFSMonitorHandle * handle;

  Monitor_place = g_malloc(sizeof(Monitor_places));
  Monitor_place->data = data;
  Monitor_place->callback = callback;
  Monitor_place->box = box;
  const char *homedir = g_getenv("HOME");

  if (!homedir)
    homedir = g_get_home_dir();

  char *  filename = g_strdup_printf("%s/.gtk-bookmarks", homedir);

  if (gnome_vfs_monitor_add(&handle, filename, GNOME_VFS_MONITOR_FILE,
                            monitor_places_callback, Monitor_place) != GNOME_VFS_OK)
  {
    printf("attempt to monitor '%s' failed \n", filename);
  }

  g_free(filename);
}

GSList* get_menu_data(gboolean show_search, gboolean show_run, gboolean show_places, gboolean show_logout, char* file_manager, char*logout)
{
  /*FIXME... I'm leaking a bit of memory here */

  Menu_list_item * dir_item;
  GSList*  data = NULL;
  GMenuTree *  menu_tree;
  const char * menu_file[] = {"gnomecc.menu", "preferences.menu", "settings.menu", NULL};//
  GMenuTreeDirectory *root;
  int i;

  if (!gnome_vfs_initialized())
    gnome_vfs_init();

  G_file_manager = file_manager;

  menu_tree = gmenu_tree_lookup("applications.menu", GMENU_TREE_FLAGS_NONE);

  if (menu_tree)
  {
    root = gmenu_tree_get_root_directory(menu_tree);

    if (root)
    {
      fill_er_up(root, &data);
      gmenu_tree_item_unref(root);
    }
  }


  data = g_slist_prepend(data, get_blank());

  data = g_slist_append(data, get_separator());

  menu_tree = gmenu_tree_lookup("gnomecc.menu", GMENU_TREE_FLAGS_NONE);

  if (menu_tree)
  {
    root = gmenu_tree_get_root_directory(menu_tree);

    if (root)
    {
      dir_item = g_malloc(sizeof(Menu_list_item));
      dir_item->item_type = MENU_ITEM_DIRECTORY;
      dir_item->name = g_strdup("Control Centre");
      dir_item->comment = g_strdup("Gnome Control Centre");
      dir_item->null = NULL;
      dir_item->sublist = NULL;
      dir_item->icon = g_strdup("gnome-control-center");
      data = g_slist_append(data, dir_item);

      fill_er_up(root, &dir_item->sublist);
      dir_item->sublist = g_slist_prepend(dir_item->sublist, get_blank());
      dir_item->sublist = g_slist_append(dir_item->sublist, get_blank());
      gmenu_tree_item_unref(root);
    }
  }

  menu_tree = gmenu_tree_lookup("settings.menu", GMENU_TREE_FLAGS_NONE);

  if (menu_tree)
  {
    root = gmenu_tree_get_root_directory(menu_tree);

    if (root)
    {
      dir_item = g_malloc(sizeof(Menu_list_item));
      dir_item->item_type = MENU_ITEM_DIRECTORY;
      dir_item->name = g_strdup("Settings");
      dir_item->comment = g_strdup("System Settings");
      dir_item->sublist = NULL;
      dir_item->null = NULL;
      dir_item->icon = g_strdup("gnome-settings");
      data = g_slist_append(data, dir_item);

      fill_er_up(root, &dir_item->sublist);
      dir_item->sublist = g_slist_prepend(dir_item->sublist, get_blank());
      dir_item->sublist = g_slist_append(dir_item->sublist, get_blank());
      gmenu_tree_item_unref(root);
    }
  }

  data = g_slist_append(data, get_separator());


  if (show_places)
  {
    dir_item = g_malloc(sizeof(Menu_list_item));
    dir_item->item_type = MENU_ITEM_DIRECTORY;
    dir_item->name = g_strdup("Places");
    dir_item->icon = g_strdup("bookmark");
    dir_item->comment = g_strdup("Your special places :-)");
    dir_item->sublist = NULL;
    dir_item->monitor = monitor_places;
    data = g_slist_append(data, dir_item);
    update_places(&dir_item->sublist, file_manager);
  }

  if (show_search)
  {
    dir_item = g_malloc(sizeof(Menu_list_item));
    dir_item->item_type = MENU_ITEM_SEARCH;
    dir_item->name = g_strdup("Find:");
    dir_item->icon = g_strdup("stock_search");
    dir_item->comment = g_strdup("Search");
    dir_item->sublist = NULL;
    dir_item->search_entry = NULL;
    data = g_slist_append(data, dir_item);
  }

  if (show_run)
  {
    dir_item = g_malloc(sizeof(Menu_list_item));
    dir_item->item_type = MENU_ITEM_RUN;
    dir_item->name = g_strdup("Run:");
    dir_item->icon = g_strdup("exec");
    dir_item->comment = g_strdup("Run a program");
    dir_item->sublist = NULL;
    dir_item->search_entry = NULL;
    data = g_slist_append(data, dir_item);

  }



  if (show_logout)
  {
    dir_item = g_malloc(sizeof(Menu_list_item));
    dir_item->item_type = MENU_ITEM_ENTRY;
    dir_item->name = g_strdup("Logout...");
    dir_item->icon = g_strdup("gnome-logout");
    dir_item->exec = g_strdup(logout);
    dir_item->desktop = g_strdup("");
    dir_item->comment = g_strdup("Logout and related activities.");
    dir_item->sublist = NULL;
    data = g_slist_append(data, dir_item);

  }

  data = g_slist_append(data, get_blank());

  return data;
}


gboolean display_message(gchar * summary, gchar * body, glong timeout)
{

  notify_message(summary, body, NULL, -1);
  return FALSE;
}


