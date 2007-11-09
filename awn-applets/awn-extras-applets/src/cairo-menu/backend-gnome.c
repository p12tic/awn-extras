/*
 * Copyright (c) 2007   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
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


#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <string.h>
#include <glib.h>
#include <assert.h>
#include <libgen.h>
#include <ctype.h>

#include "menu_list_item.h"


static void print_directory (GMenuTreeDirectory *directory);
static void print_entry (GMenuTreeEntry *entry,const char *path);
static char *make_path (GMenuTreeDirectory *directory);
static void append_directory_path (GMenuTreeDirectory *directory,GString *path);




static void
append_directory_path (GMenuTreeDirectory *directory,
		       GString            *path)
{
  GMenuTreeDirectory *parent;

  parent = gmenu_tree_item_get_parent (GMENU_TREE_ITEM (directory));

  if (!parent)
    {
      g_string_append_c (path, '/');
      return;
    }

  append_directory_path (parent, path);

  g_string_append (path, gmenu_tree_directory_get_name (directory));
  g_string_append_c (path, '/');

  gmenu_tree_item_unref (parent);
}

static char *
make_path (GMenuTreeDirectory *directory)
{
  GString *path;

  g_return_val_if_fail (directory != NULL, NULL);

  path = g_string_new (NULL);

  append_directory_path (directory, path);

  return g_string_free (path, FALSE);
}

static void
print_entry (GMenuTreeEntry *entry,
	     const char     *path)
{
  char *utf8_path;
  char *utf8_file_id;

  utf8_path = g_filename_to_utf8 (gmenu_tree_entry_get_desktop_file_path (entry),
				  -1, NULL, NULL, NULL);

  utf8_file_id = g_filename_to_utf8 (gmenu_tree_entry_get_desktop_file_id (entry),
				     -1, NULL, NULL, NULL);

  g_print ("%s\t%s\t%s%s\n",
	   path,
	   utf8_file_id ? utf8_file_id : _("Invalid desktop file ID"),
	   utf8_path ? utf8_path : _("[Invalid Filename]"),
	   gmenu_tree_entry_get_is_excluded (entry) ? _(" <excluded>") : "");

  g_free (utf8_file_id);
  g_free (utf8_path);
}

static void
print_directory (GMenuTreeDirectory *directory)
{
  GSList     *items;
  GSList     *tmp;
  const char *path;
  char       *freeme;

  freeme = make_path (directory);
  if (!strcmp (freeme, "/"))
    path = freeme;
  else
    path = freeme + 1;

  items = gmenu_tree_directory_get_contents (directory);

  tmp = items;
  while (tmp != NULL)
    {
      GMenuTreeItem *item = tmp->data;

      switch (gmenu_tree_item_get_type (item))
	{
	case GMENU_TREE_ITEM_ENTRY:
	  print_entry (GMENU_TREE_ENTRY (item), path);
	  break;

	case GMENU_TREE_ITEM_DIRECTORY:
	  print_directory (GMENU_TREE_DIRECTORY (item));
	  break;

	case GMENU_TREE_ITEM_HEADER:
	case GMENU_TREE_ITEM_SEPARATOR:
	  break;

	case GMENU_TREE_ITEM_ALIAS:
	  {
	    GMenuTreeItem *aliased_item;

	    aliased_item = gmenu_tree_alias_get_item (GMENU_TREE_ALIAS (item));
	    if (gmenu_tree_item_get_type (aliased_item) == GMENU_TREE_ITEM_ENTRY)
	      print_entry (GMENU_TREE_ENTRY (aliased_item), path);
	  }
	  break;

	default:
	  g_assert_not_reached ();
	  break;
	}

      gmenu_tree_item_unref (tmp->data);

      tmp = tmp->next;
    }

	g_slist_free (items);

	g_free (freeme);
}

static void
add_entry (GMenuTreeEntry *entry,
	     const char     *path,GSList**p)
{
	GSList*		data=*p;
	char *utf8_path;
	char *utf8_file_id;
	Menu_list_item * item;
	gchar * file_name;
	
	utf8_path = g_filename_to_utf8 (gmenu_tree_entry_get_desktop_file_path (entry),
				  -1, NULL, NULL, NULL);

	utf8_file_id = g_filename_to_utf8 (gmenu_tree_entry_get_desktop_file_id (entry),
					 -1, NULL, NULL, NULL);
	file_name=utf8_path ? utf8_path : _("[Invalid Filename]");
	item=g_malloc(sizeof(Menu_list_item));
	item->item_type=MENU_ITEM_ENTRY;
	item->name=gmenu_tree_entry_get_name(entry);
	item->icon=gmenu_tree_entry_get_icon(entry);	
	item->exec=gmenu_tree_entry_get_exec(entry);	
	item->comment=gmenu_tree_entry_get_comment(entry);	
	item->launch_in_terminal=gmenu_tree_entry_get_launch_in_terminal(entry);
	item->desktop=g_strdup(file_name);
	data=g_slist_append(data,item);
	*p=data;

	g_free (utf8_file_id);
	g_free (utf8_path);
}


static void
fill_er_up(GMenuTreeDirectory *directory,GSList**p)
{
	GSList*		data=*p;
	GSList     *items;
	GSList     *tmp;
	const char *path;
	char       *freeme;
	
	freeme = make_path (directory);
	if (!strcmp (freeme, "/"))
		path = freeme;
  	else
    	path = freeme + 1;

  	items = gmenu_tree_directory_get_contents (directory);

  	tmp = items;
  	while (tmp != NULL)
    {
      	GMenuTreeItem *item = tmp->data;

      	switch (gmenu_tree_item_get_type (item))
		{
			case GMENU_TREE_ITEM_ENTRY:
	  		//	print_entry (GMENU_TREE_ENTRY (item), path);
				add_entry(GMENU_TREE_ENTRY (item), path,&data);
	  			break;

			case GMENU_TREE_ITEM_DIRECTORY:
				{
					Menu_list_item * dir_item;			
					dir_item=g_malloc(sizeof(Menu_list_item));
					dir_item->item_type=MENU_ITEM_DIRECTORY;
					dir_item->name=gmenu_tree_directory_get_name(item);
					dir_item->desktop=gmenu_tree_directory_get_desktop_file_path(item);
//					dir_item->comment=gmenu_tree_directory_get_comment(item);
//it seems gmenu_tree_directory_get_icon is broken in some way. or mabye it's my code
#if 1
					dir_item->icon=gmenu_tree_directory_get_icon(item);
#else
					dir_item->icon=g_strdup(dir_item->name);
#endif					
					dir_item->sublist=NULL;
					data=g_slist_append(data,dir_item);
					fill_er_up(GMENU_TREE_DIRECTORY (item),&dir_item->sublist);
				}	

				break;

			case GMENU_TREE_ITEM_HEADER:
			case GMENU_TREE_ITEM_SEPARATOR:
			  	break;

			case GMENU_TREE_ITEM_ALIAS:
/*			  	{
					GMenuTreeItem *aliased_item;

					aliased_item = gmenu_tree_alias_get_item (GMENU_TREE_ALIAS (item));
					if (gmenu_tree_item_get_type (aliased_item) == GMENU_TREE_ITEM_ENTRY)
				  		print_entry (GMENU_TREE_ENTRY (aliased_item), path);
			  	}*/
			  	break;

			default:
			  	g_assert_not_reached ();
			  	break;
		}

      	gmenu_tree_item_unref (tmp->data);

      	tmp = tmp->next;
    }

	g_slist_free (items);

	g_free (freeme);
	*p=data;
}


GSList* get_menu_data(gboolean show_search,gboolean show_run,gboolean show_places,char* file_manager)
{
/*FIXME... I'm leaking a bit of memory her */

	Menu_list_item * dir_item;
	GSList*		data=NULL;
	GMenuTree *  menu_tree;
	const char * menu_file[]={"gnomecc.menu","preferences.menu","settings.menu",NULL};//
	GMenuTreeDirectory *root;
	int i;	

	menu_tree=gmenu_tree_lookup ("applications.menu",GMENU_TREE_FLAGS_NONE);
	if (menu_tree)
	{
		root = gmenu_tree_get_root_directory (menu_tree);	
		fill_er_up(root,&data);
		gmenu_tree_item_unref (root);		
	}
	
	menu_tree=gmenu_tree_lookup ("gnomecc.menu",GMENU_TREE_FLAGS_NONE);	
	if (menu_tree)
	{
		dir_item=g_malloc(sizeof(Menu_list_item));
		dir_item->item_type=MENU_ITEM_DIRECTORY;
		dir_item->name=g_strdup("Control Centre");
		dir_item->comment=g_strdup("Gnome Control Centre");				
		dir_item->sublist=NULL;
		dir_item->icon=g_strdup("gnome-control-center");
		data=g_slist_append(data,dir_item);

		root = gmenu_tree_get_root_directory (menu_tree);	
		fill_er_up(root,&dir_item->sublist);
		gmenu_tree_item_unref (root);		
	}
	
	menu_tree=gmenu_tree_lookup ("settings.menu",GMENU_TREE_FLAGS_NONE);	
	if (menu_tree)
	{
		dir_item=g_malloc(sizeof(Menu_list_item));
		dir_item->item_type=MENU_ITEM_DIRECTORY;
		dir_item->name=g_strdup("Settings");
		dir_item->comment=g_strdup("System Settings");		
		dir_item->sublist=NULL;
		dir_item->icon=g_strdup("gnome-settings");
		data=g_slist_append(data,dir_item);
		root = gmenu_tree_get_root_directory (menu_tree);	
		fill_er_up(root,&dir_item->sublist);
		gmenu_tree_item_unref (root);		
	}


	if (show_places)
	{
		dir_item=g_malloc(sizeof(Menu_list_item));
		dir_item->item_type=MENU_ITEM_DIRECTORY;
		dir_item->name=g_strdup("Places");
		dir_item->icon=g_strdup("bookmark");
		dir_item->comment=g_strdup("Your special places :-)");
		dir_item->sublist=NULL;
		dir_item->search_entry=NULL;	
		data=g_slist_append(data,dir_item);
			
		Menu_list_item * item;	
		item=g_malloc(sizeof(Menu_list_item));	
		item->item_type=MENU_ITEM_ENTRY;
		item->name=g_strdup("Home");
		item->icon=g_strdup("stock_home");
		const char *homedir = g_getenv ("HOME");
		if (!homedir)
     		homedir = g_get_homedir ();
		item->exec=g_strdup_printf("%s %s",file_manager,homedir);			
		item->comment=g_strdup("Your Home Directory");
		item->desktop=g_strdup("");			
		dir_item->sublist=g_slist_append(dir_item->sublist,item);
		
		item=g_malloc(sizeof(Menu_list_item));	
		item->item_type=MENU_ITEM_ENTRY;
		item->name=g_strdup("File System");
		item->icon=g_strdup("stock_folder");
		item->exec=g_strdup_printf("%s /",file_manager);			
		item->comment=g_strdup("Root File System");
		item->desktop=g_strdup("");			
		dir_item->sublist=g_slist_append(dir_item->sublist,item);
		#if 1
		FILE*	handle;
		char *  filename=g_strdup_printf("%s/.gtk-bookmarks",homedir);
		handle=g_fopen(filename,"r");
		if (handle)
		{
			char *	line=NULL;
			char *  len=0;
			while ( getline(&line,&len,handle) != -1)	
			{
					char *p;
					p=line+strlen(line);
					if (p!=line)
					{
						while ( !isalpha(*p) && (p!=line))
						{
							*p='\0';
							p--;
						}							
						while( (*p!='/') && (p!=line) )
							p--;
						if (p!=line)
						{
							p++;
							item=g_malloc(sizeof(Menu_list_item));	
							item->item_type=MENU_ITEM_ENTRY;
							item->name=g_strdup(p);
							item->icon=g_strdup(p);
							item->exec=g_strdup_printf("%s %s",file_manager,line);			
							item->comment=g_strdup(line);
							item->desktop=g_strdup("");			
							dir_item->sublist=g_slist_append(dir_item->sublist,item);								
						}												
					}
					free(line);
					line=NULL;
			}
			fclose(handle);
			g_free(filename);
		}			
		#endif		
	}

	if (show_search)
	{
		dir_item=g_malloc(sizeof(Menu_list_item));
		dir_item->item_type=MENU_ITEM_SEARCH;
		dir_item->name=g_strdup("Find:");
		dir_item->icon=g_strdup("stock_search");
		dir_item->comment=g_strdup("Search");		
		dir_item->sublist=NULL;
		dir_item->search_entry=NULL;	
		data=g_slist_append(data,dir_item);
	}
	
	if (show_run)
	{
		dir_item=g_malloc(sizeof(Menu_list_item));
		dir_item->item_type=MENU_ITEM_RUN;
		dir_item->name=g_strdup("Run:");
		dir_item->icon=g_strdup("stock_run");
		dir_item->comment=g_strdup("Run a program");		
		dir_item->sublist=NULL;
		dir_item->search_entry=NULL;	
		data=g_slist_append(data,dir_item);

	}	
	return data;
}	
