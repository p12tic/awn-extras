/*
 * Copyright (C) 2008 Rodney Cryderman <rcryderman@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Library General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA
 */

#include <gtk/gtk.h>
#include "awn-extras.h"

typedef struct
{
  gchar * instance;
  gchar * base;
  gchar * applet_name;
} PrefsLocation;  

static gboolean 
_start_applet_prefs(GtkMenuItem *menuitem,PrefsLocation  * prefs_location)
{ 
  GError *err = NULL;
  gchar * editor = "gconf-editor";  //temporary...
  gchar * folder = "/apps/avant-window-navigator/applets/"; //temporary
  gchar * cmdline;
  cmdline = g_strdup_printf("%s %s%s", editor, folder, prefs_location->instance);
  g_printf("1) launching... %s\n", cmdline);
  g_spawn_command_line_async(cmdline, &err);//FIXME
  if (err)
  {
    g_warning("Failed to launch applet preferences dialog (%s): %s\n", cmdline, err->message);
    g_error_free(err);
  }
  g_free(cmdline);
  
  if (prefs_location->base)
  {
    cmdline = g_strdup_printf("%s %s%s", editor, folder, prefs_location->base);
    g_printf("2) launching... %s\n", cmdline);    
    g_spawn_command_line_async(cmdline, &err);//FIXME
    if (err)
    {
      g_warning("Failed to launch applet preferences dialog (%s): %s\n", cmdline, err->message);
      g_error_free(err);
    }
    g_free(cmdline);    
  }
  return TRUE;
}


static gboolean
_cleanup_applet_prefs_item(GtkWidget *widget, GdkEvent *event,
                           PrefsLocation  * prefs_location)
{
  g_free(prefs_location->instance);  
  g_free(prefs_location->base);
  g_free(prefs_location->applet_name);
  g_free(prefs_location);
  return FALSE;
}

/*
* Create a menu item that invokes a generic applet preferences dialog.
* instance - The folder name containing the configuration key within the applets
* configuration folder.
* baseconf - If there is a default configuration location that is different than
* the instance provided.  Otherwise NULL.
* applet_name - applet name used to reference the associated schema-ini
*
*  Returns:
*    A gtk_menu_item or NULL if the generic applet preferences configuration is
*    disabled
*
*  Notes:
*    There is no need to attach the returned item to a
*  signal as this is handled by the function.
*/
GtkWidget * shared_menuitem_create_applet_prefs(gchar * instance, 
                                          gchar * baseconf,gchar * applet_name)
{
  g_return_val_if_fail(instance,NULL);
  g_return_val_if_fail(applet_name,NULL);    
  
  GtkWidget * item = NULL;
  gchar * keysdir_copy = NULL;
  PrefsLocation  * prefs_location = g_malloc(sizeof(PrefsLocation));
  
  prefs_location->instance = g_strdup(instance);
  prefs_location->base = baseconf?g_strdup(baseconf):NULL; 
  prefs_location->applet_name = g_strdup(applet_name);
  if (share_config_bool(SHR_KEY_GENERIC_PREFS))
  {
    item = gtk_image_menu_item_new_with_label("Applet Preferences");
    gtk_widget_show_all(item);
    g_signal_connect(G_OBJECT(item), "activate",
                     G_CALLBACK(_start_applet_prefs), prefs_location);
    g_signal_connect(G_OBJECT(item), "destroy-event",
                     G_CALLBACK(_cleanup_applet_prefs_item), prefs_location);
  }
  else
  {
      g_warning("Generic Preferences Requested but support is not enabled in configuration\n");
  }
 
  return item;
}

/*-----------------------------------------------------------*/

static gboolean 
_show_about(GtkMenuItem *menuitem,GtkWidget * dialog)
{
  gtk_widget_show_all(dialog); 
}

static gboolean
_cleanup_about(GtkWidget *widget, GdkEvent *event,
                           GtkWidget * dialog)
{
  gtk_widget_destroy(dialog); 
}

/* 
*  see GtkAboutDialog() for a description of args other than license.
*   license must be one of the values enumerated in AwnAppletLicense.
*   copyright,license and program_name are mandatory.
*  Returns:
*    A about applet gtk_menu_item 
*/
GtkWidget *shared_menuitem_about_applet(const gchar * copyright,
                                        AwnAppletLicense license,
                                        const gchar * program_name,
                                        const gchar * version,                                        
                                        const gchar * comments,
                                        const gchar * website,
                                        const gchar * website_label,
                                        const gchar * icon_name,                                        
                                        const gchar * translator_credits,                                        
                                        const gchar **authors,
                                        const gchar **artists,
                                        const gchar **documenters)
{
  //we could use  gtk_show_about_dialog()... but no.
  GtkAboutDialog *dialog=GTK_ABOUT_DIALOG(gtk_about_dialog_new ());
  GtkWidget *item;
  gchar * item_text=NULL;
  
  g_assert(copyright!=NULL);
  g_assert(strlen(copyright)>8);
  g_assert(program_name);
  if (copyright)
  {
    gtk_about_dialog_set_copyright (dialog,copyright);
  }
  switch(license)   //FIXME... insert more complete license info.
  {
    case AWN_APPLET_LICENSE_GPLV2:
      gtk_about_dialog_set_license (dialog,"GPLv2");    
      break;    
    case AWN_APPLET_LICENSE_GPLV3:
      gtk_about_dialog_set_license (dialog,"GPLv3");    
      break;    
    case AWN_APPLET_LICENSE_LGPLV2_1:
      gtk_about_dialog_set_license (dialog,"LGPLv2.1");    
      break;    
    case AWN_APPLET_LICENSE_LGPLV3:
      gtk_about_dialog_set_license (dialog,"LGPLv3");
      break;
    default:
      g_warning("License must be set\n");
      g_assert_not_reached ();
  }
  if (program_name)
  {
    gtk_about_dialog_set_program_name (dialog,program_name);
  }
  if (version)    //we can probably append some addition build info in here...
  {
    gtk_about_dialog_set_version (dialog,version);
  }
  if (comments)
  {
    gtk_about_dialog_set_comments (dialog,comments);
  }
  if (website)
  {
    gtk_about_dialog_set_website (dialog,website);
  }
  if (website_label)
  {
    gtk_about_dialog_set_website_label (dialog,website_label);
  }
  if (icon_name)
  {
    gtk_about_dialog_set_logo_icon_name (dialog,icon_name);
  }
  if (translator_credits)
  {
    gtk_about_dialog_set_translator_credits (dialog,translator_credits);
  }
  if (authors)
  {
    gtk_about_dialog_set_authors (dialog,authors);
  }
  if (artists)
  {
    gtk_about_dialog_set_artists (dialog,artists);
  }
  if (documenters)
  {
    gtk_about_dialog_set_documenters (dialog,documenters);
  }  
  item_text = g_strdup_printf("About %s",program_name);
  item = gtk_image_menu_item_new_with_label(item_text); //FIXME Add pretty icon
  g_free(item_text);

  gtk_widget_show_all(item);
  g_signal_connect(G_OBJECT(item), "activate",
                   G_CALLBACK(_show_about), dialog);
  g_signal_connect(G_OBJECT(item), "destroy-event",
                   G_CALLBACK(_cleanup_about), dialog);
  g_signal_connect_swapped (dialog, "response",
                   G_CALLBACK (gtk_widget_hide),dialog);  
  return item;
}

GtkWidget *shared_menuitem_about_applet_simple(const gchar * copyright,
                                        AwnAppletLicense license,
                                        const gchar * program_name,
                                        const gchar * version)
{  
  return  shared_menuitem_about_applet(copyright,
                                       license,
                                       program_name,
                                       version,
                                       NULL,
                                       NULL,
                                       NULL,
                                       NULL,
                                       NULL,
                                       NULL,
                                       NULL,
                                       NULL);
}
