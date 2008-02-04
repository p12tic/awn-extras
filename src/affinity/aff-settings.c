/*
 *  Copyright (C) 2007 Neil Jagdish Patel <njpatel@gmail.com>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
 *  Author : Neil Jagdish Patel <njpatel@gmail.com>
*/

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <glib/gi18n.h>
#include "aff-settings.h"

/* globals */
static AffSettings *settings		= NULL;
static AwnConfigClient *client 		= NULL;

/* prototypes */
static void aff_load_bool        (AwnConfigClient *client, const gchar *group, const gchar *key, gboolean *data, gboolean def);
static void aff_load_string      (AwnConfigClient *client, const gchar *group, const gchar *key, gchar **data,   const gchar *def);
static void aff_load_float       (AwnConfigClient *client, const gchar *group, const gchar *key, gfloat *data,   gfloat def);
static void aff_load_int         (AwnConfigClient *client, const gchar *group, const gchar *key, gint *data,     gint def);
static void aff_load_color       (AwnConfigClient *client, const gchar *group, const gchar *key, AffColor *data, const char * def);
static void aff_load_string_list (AwnConfigClient *client, const gchar *group, const gchar *key, GSList **data,  GSList *def);

static void aff_notify_bool   (AwnConfigClientNotifyEntry *entry, gboolean *data);
static void aff_notify_string (AwnConfigClientNotifyEntry *entry, gchar **data);
static void aff_notify_float  (AwnConfigClientNotifyEntry *entry, gfloat *data);
static void aff_notify_int    (AwnConfigClientNotifyEntry *entry, gint *data);
static void aff_notify_color  (AwnConfigClientNotifyEntry *entry, AffColor *color);

static void hex2float(char* HexColor, float* FloatColor);

#define AFF_KEY			"global_key_binding"
#define AFF_WINX		"window_xpos"
#define AFF_WINY		"window_ypos"
#define AFF_FAVS		"favourites"

#define COL_PATH		"colors"				/*color*/
#define COL_ROUNDED		"rounded_corners"		/*bool*/		
#define COL_BACK_STEP_1		"back_step_1"		/*color*/
#define COL_BACK_STEP_2		"back_step_2"		/*color*/
#define COL_HIGH_STEP_1		"high_step_1"		/*color*/
#define COL_HIGH_STEP_2		"high_step_2"		/*color*/
#define COL_HIGHLIGHT		"highlight"		/*color*/
#define COL_BORDER		"border"			/*color*/
#define COL_WIDGET_BORDER	"widget_border"		/*color*/
#define COL_WIDGET_HIGHLIGHT	"widget_highlight"	/*color*/
#define COL_TEXT_COLOR		"text_color" 		/*string*/

#define FILT_PATH               "filters"
#define FILT_APPS               "applications"           /*CSV*/
#define FILT_BOOKS              "bookmarks"              /*CSV*/
#define FILT_CONTACTS           "contacts"               /*CSV*/
#define FILT_DOCS               "documents"              /*CSV*/
#define FILT_EMAILS             "emails"                 /*CSV*/
#define FILT_IMAGES             "images"                 /*CSV*/
#define FILT_MUSIC              "music"                  /*CSV*/
#define FILT_VIDS               "vids"                   /*CSV*/

#define SYS_PATH                "system"
#define SYS_SOFTWARE            "config_software"         /*command line*/
#define SYS_CONTROL_PANEL       "control_panel"           /*command line*/
#define SYS_LOCK_SCREEN         "lock_screen"             /*command line*/
#define SYS_LOG_OUT             "log_out"                 /*command line*/
#define SYS_OPEN_URI            "open_uri"                /*command line*/
#define SYS_FILE_MAN            "file_manager"            /*command line*/
#define SYS_COMPUTER            "computer"                /*command line*/
#define SYS_NETWORK             "network"                 /*command line*/

#define APPLET_PATH             "applet"
#define APPLET_ICON             "icon"                    /*string*/
#define APPLET_NAME             "name"                    /*string*/

AffSettings* 
aff_settings_new()
{
	AffSettings *s = NULL;
	
	s = g_new(AffSettings, 1);
	settings = s;
	client = awn_config_client_new_for_applet ("affinity", NULL);
	
	/* app stuff */
	awn_config_client_ensure_group (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP);
	aff_load_string (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP, AFF_KEY, &s->key_binding, "<Control><Alt>a");
	aff_load_int    (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP, AFF_WINX , &s->window_x, 100);
	aff_load_int    (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP, AFF_WINY, &s->window_y, 100);
	aff_load_string (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP, AFF_FAVS , &s->favourites, "");
		
	/* system calls */
	awn_config_client_ensure_group (client, SYS_PATH);
	aff_load_string(client, SYS_PATH, SYS_SOFTWARE , &s->config_software, "pirut");
	aff_load_string(client, SYS_PATH, SYS_CONTROL_PANEL , &s->control_panel, "gnome-control-center");
	aff_load_string(client, SYS_PATH, SYS_LOCK_SCREEN , &s->lock_screen, "gnome-screensaver-command --lock");
	aff_load_string(client, SYS_PATH, SYS_LOG_OUT , &s->log_out, "gnome-session-save --kill --gui");	
	aff_load_string(client, SYS_PATH, SYS_OPEN_URI , &s->open_uri, "gnome-open");	
	aff_load_string(client, SYS_PATH, SYS_FILE_MAN , &s->file_manager, "nautilus");	
	aff_load_string(client, SYS_PATH, SYS_COMPUTER , &s->computer, "Computer:///");	
	aff_load_string(client, SYS_PATH, SYS_NETWORK , &s->network, "Network:///");		

	
	/* filters */
	awn_config_client_ensure_group (client, FILT_PATH);
	aff_load_string (client, FILT_PATH, FILT_APPS , &s->apps, "apps");
	aff_load_string (client, FILT_PATH, FILT_BOOKS, &s->books, "books");
	aff_load_string (client, FILT_PATH, FILT_CONTACTS, &s->contacts, "contacts,people");
	aff_load_string (client, FILT_PATH, FILT_DOCS, &s->docs, "docs");		
	aff_load_string (client, FILT_PATH, FILT_EMAILS, &s->emails, "emails");
	aff_load_string (client, FILT_PATH, FILT_IMAGES, &s->images, "pics,images");
	aff_load_string (client, FILT_PATH, FILT_MUSIC, &s->music, "music,audio");
	aff_load_string (client, FILT_PATH, FILT_VIDS, &s->vids, "movies,vids");
		
			
	/* Appearence */
	awn_config_client_ensure_group (client, COL_PATH);
	aff_load_bool   (client, COL_PATH, COL_ROUNDED, &s->rounded_corners, FALSE);
	aff_load_color  (client, COL_PATH, COL_BACK_STEP_1, &s->back_step_1, "A1A8BBEC");
	aff_load_color  (client, COL_PATH, COL_BACK_STEP_2, &s->back_step_2, "141E3CF3");
	aff_load_color  (client, COL_PATH, COL_HIGH_STEP_1, &s->hi_step_1, "FFFFFF4E");
	aff_load_color  (client, COL_PATH, COL_HIGH_STEP_2, &s->hi_step_2, "FFFFFF55");

	aff_load_color  (client, COL_PATH, COL_HIGHLIGHT, &s->highlight, "FFFFFF28");
	aff_load_color  (client, COL_PATH, COL_BORDER, &s->border, "00151FE0");
	aff_load_color  (client, COL_PATH, COL_WIDGET_BORDER, &s->widget_border, "00000099");
	aff_load_color  (client, COL_PATH, COL_WIDGET_HIGHLIGHT, &s->widget_highlight, "FFFFFF50");	
	
	aff_load_string (client, COL_PATH, COL_TEXT_COLOR, &s->text_color, "#ffffff");
	
	/* applet specific */
	awn_config_client_ensure_group (client, APPLET_PATH);
	aff_load_string (client, APPLET_PATH, APPLET_ICON, &s->applet_icon, "gnome-main-menu");
	aff_load_string (client, APPLET_PATH, APPLET_NAME, &s->applet_name, _("Computer"));	
	
	/* Make user dome directory */
	gchar *dir = NULL;
	dir = g_strdup_printf("%s/affinity/actions", g_get_user_config_dir ());
	if (!g_file_test (dir, G_FILE_TEST_EXISTS)) {
		g_mkdir_with_parents (dir, 0755);
	}
	
	return s;
}

AffSettings* 
aff_Settings_get_default (void)
{
        return settings;
}

AwnConfigClient *
aff_settings_get_client (void)
{
	return client;
}

static void 
aff_notify_bool (AwnConfigClientNotifyEntry *entry, gboolean* data)
{
	*data = entry->value.bool_val;
}

static void 
aff_notify_string (AwnConfigClientNotifyEntry *entry, gchar** data)
{
	*data = g_strdup (entry->value.str_val);
}

static void 
aff_notify_float (AwnConfigClientNotifyEntry *entry, gfloat* data)
{
	*data = entry->value.float_val;
}

static void 
aff_notify_int (AwnConfigClientNotifyEntry *entry, gint* data)
{
	*data = entry->value.int_val;
}

static void 
aff_notify_color (AwnConfigClientNotifyEntry *entry, AffColor* color)
{
	float colors[4];

	hex2float (entry->value.str_val, colors);

	color->red = colors[0];
	color->green = colors[1];
	color->blue = colors[2];
	color->alpha = colors[3];
}


static void
aff_load_bool (AwnConfigClient *client, const gchar *group, const gchar *key, gboolean *data, gboolean def)
{
	if (awn_config_client_entry_exists (client, group, key)) {
		*data = awn_config_client_get_bool (client, group, key, NULL);
	} else {
		g_message ("%s/%s unset, setting now", group, key);
		awn_config_client_set_bool (client, group, key, def, NULL);
		*data = def;
	}
	awn_config_client_notify_add (client, group, key, (AwnConfigClientNotifyFunc)aff_notify_bool, data);
}

static void
aff_load_string (AwnConfigClient *client, const gchar *group, const gchar *key, gchar **data, const gchar *def)
{
	if (awn_config_client_entry_exists (client, group, key)) {
		*data = awn_config_client_get_string (client, group, key, NULL);
	} else {
		g_message ("%s/%s unset, setting now\n", group, key);
		awn_config_client_set_string (client, group, key, (gchar*)def, NULL);
		*data = g_strdup(def);
	}
	awn_config_client_notify_add (client, group, key, (AwnConfigClientNotifyFunc)aff_notify_string, data);
}

static void
aff_load_float (AwnConfigClient *client, const gchar *group, const gchar *key, gfloat *data, float def)
{
	if (awn_config_client_entry_exists (client, group, key)) {
		*data = awn_config_client_get_float (client, group, key, NULL);
	} else {
		g_message ("%s unset, setting now\n", key);
		awn_config_client_set_float (client, group, key, def, NULL);
		*data = def;
	}
	awn_config_client_notify_add (client, group, key, (AwnConfigClientNotifyFunc)aff_notify_float, data);
}

static void
aff_load_int (AwnConfigClient *client, const gchar *group, const gchar *key, gint *data, int def)
{
	if (awn_config_client_entry_exists (client, group, key)) {
		*data = awn_config_client_get_int (client, group, key, NULL);
	} else {
		g_message ("%s/%s unset, setting now\n", group, key);
		awn_config_client_set_int (client, group, key, def, NULL);
		*data = def;
	}
	awn_config_client_notify_add (client, group, key, (AwnConfigClientNotifyFunc)aff_notify_int, data);
}

static void
aff_load_color (AwnConfigClient *client, const gchar *group, const gchar *key, AffColor *color, const gchar *def)
{
	float colors[4];

	if (awn_config_client_entry_exists (client, group, key)) {
		hex2float (awn_config_client_get_string (client, group, key, NULL), colors);
		color->red = colors[0];
		color->green = colors[1];
		color->blue = colors[2];
		color->alpha = colors[3];
	} else {
		g_message ("%s/%s unset, setting now\n", group, key);
		awn_config_client_set_string (client, group, key, (gchar*)def, NULL);
		hex2float ( (gchar*)def, colors);
		color->red = colors[0];
		color->green = colors[1];
		color->blue = colors[2];
		color->alpha = colors[3];
	}
		
	awn_config_client_notify_add (client, group, key, (AwnConfigClientNotifyFunc)aff_notify_color, color);
}

static void
aff_load_string_list (AwnConfigClient *client, const gchar *group, const gchar* key, GSList **data, GSList *def)
{
	if (awn_config_client_entry_exists (client, group, key)) {
		*data = awn_config_client_get_list (client, group, key, AWN_CONFIG_CLIENT_LIST_TYPE_STRING, NULL);
	} else {
		g_message ("%s/%s unset, setting now\n", group, key);
		awn_config_client_set_list (client, group, key, AWN_CONFIG_CLIENT_LIST_TYPE_STRING, def, NULL);
		*data = def;
	}
}

static int 
getdec(char hexchar)
{
   if ((hexchar >= '0') && (hexchar <= '9')) return hexchar - '0';
   if ((hexchar >= 'A') && (hexchar <= 'F')) return hexchar - 'A' + 10;
   if ((hexchar >= 'a') && (hexchar <= 'f')) return hexchar - 'a' + 10;

   return -1; // Wrong character

}

static void 
hex2float(char* HexColor, float* FloatColor)
{
   char* HexColorPtr = HexColor;

   int i = 0;
   for (i = 0; i < 4; i++)
   {
     int IntColor = (getdec(HexColorPtr[0]) * 16) +
                     getdec(HexColorPtr[1]);

     FloatColor[i] = (float) IntColor / 255.0;
     HexColorPtr += 2;
   }

}

