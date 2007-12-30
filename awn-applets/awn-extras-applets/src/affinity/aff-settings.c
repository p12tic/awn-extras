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

#include <libgnome/gnome-i18n.h>
#include "aff-settings.h"

/* globals */
static AffSettings *settings		= NULL;
static GConfClient *client 		= NULL;

/* prototypes */
static void aff_load_bool(GConfClient *client, const gchar* key, gboolean *data, gboolean def);
static void aff_load_string(GConfClient *client, const gchar* key, gchar **data, const char *def);
static void aff_load_float(GConfClient *client, const gchar* key, gfloat *data, float def);
static void aff_load_int(GConfClient *client, const gchar* key, int *data, int def);
static void aff_load_color(GConfClient *client, const gchar* key, AffColor *color, const char * def);
static void aff_load_string_list(GConfClient *client, const gchar* key, GSList **data, GSList *def);

static void aff_notify_bool (GConfClient *client, guint cid, GConfEntry *entry, gboolean* data);
static void aff_notify_string (GConfClient *client, guint cid, GConfEntry *entry, gchar** data);
static void aff_notify_float (GConfClient *client, guint cid, GConfEntry *entry, gfloat* data);
static void aff_load_int (GConfClient *client, const gchar* key, int *data, int def);
static void aff_notify_color (GConfClient *client, guint cid, GConfEntry *entry, AffColor *color);

static void hex2float(char* HexColor, float* FloatColor);

#define AFF_PATH		"/apps/affinity"
#define AFF_KEY			"/apps/affinity/global_key_binding"
#define AFF_WINX		"/apps/affinity/window_xpos"
#define AFF_WINY		"/apps/affinity/window_ypos"
#define AFF_FAVS		"/apps/affinity/favourites"

#define COL_PATH		"/apps/affinity/colors"				/*color*/
#define COL_ROUNDED		"/apps/affinity/colors/rounded_corners"		/*bool*/		
#define COL_BACK_STEP_1		"/apps/affinity/colors/back_step_1"		/*color*/
#define COL_BACK_STEP_2		"/apps/affinity/colors/back_step_2"		/*color*/
#define COL_HIGH_STEP_1		"/apps/affinity/colors/high_step_1"		/*color*/
#define COL_HIGH_STEP_2		"/apps/affinity/colors/high_step_2"		/*color*/
#define COL_HIGHLIGHT		"/apps/affinity/colors/highlight"		/*color*/
#define COL_BORDER		"/apps/affinity/colors/border"			/*color*/
#define COL_WIDGET_BORDER	"/apps/affinity/colors/widget_border"		/*color*/
#define COL_WIDGET_HIGHLIGHT	"/apps/affinity/colors/widget_highlight"	/*color*/
#define COL_TEXT_COLOR		"/apps/affinity/colors/text_color" 		/*string*/

#define FILT_PATH               "/apps/affinity/filters"
#define FILT_APPS               "/apps/affinity/filters/applications"           /*CSV*/
#define FILT_BOOKS              "/apps/affinity/filters/bookmarks"              /*CSV*/
#define FILT_CONTACTS           "/apps/affinity/filters/contacts"               /*CSV*/
#define FILT_DOCS               "/apps/affinity/filters/documents"              /*CSV*/
#define FILT_EMAILS             "/apps/affinity/filters/emails"                 /*CSV*/
#define FILT_IMAGES             "/apps/affinity/filters/images"                 /*CSV*/
#define FILT_MUSIC              "/apps/affinity/filters/music"                  /*CSV*/
#define FILT_VIDS               "/apps/affinity/filters/vids"                   /*CSV*/

#define SYS_PATH                "/apps/affinity/system"
#define SYS_SOFTWARE            "/apps/affinity/system/config_software"         /*command line*/
#define SYS_CONTROL_PANEL       "/apps/affinity/system/control_panel"           /*command line*/
#define SYS_LOCK_SCREEN         "/apps/affinity/system/lock_screen"             /*command line*/
#define SYS_LOG_OUT             "/apps/affinity/system/log_out"                 /*command line*/
#define SYS_OPEN_URI            "/apps/affinity/system/open_uri"                /*command line*/
#define SYS_FILE_MAN            "/apps/affinity/system/file_manager"            /*command line*/
#define SYS_COMPUTER            "/apps/affinity/system/computer"                /*command line*/
#define SYS_NETWORK             "/apps/affinity/system/network"                 /*command line*/

#define APPLET_PATH             "/apps/affinity/applet"
#define APPLET_ICON             "/apps/affinity/applet/icon"                    /*string*/
#define APPLET_NAME             "/apps/affinity/applet/name"                    /*string*/

AffSettings* 
aff_settings_new()
{
	AffSettings *s = NULL;
	
	s = g_new(AffSettings, 1);
	settings = s;
	client = gconf_client_get_default();
	
	/* app stuff */
	gconf_client_add_dir(client, AFF_PATH, GCONF_CLIENT_PRELOAD_NONE, NULL);
	aff_load_string(client, AFF_KEY , &s->key_binding, "<Control><Alt>a");
	aff_load_int (client, AFF_WINX , &s->window_x, 100);
	aff_load_int (client, AFF_WINY, &s->window_y, 100);
	aff_load_string(client, AFF_FAVS , &s->favourites, "");
		
	/* system calls */
	gconf_client_add_dir(client, SYS_PATH, GCONF_CLIENT_PRELOAD_NONE, NULL);
	aff_load_string(client, SYS_SOFTWARE , &s->config_software, "pirut");
	aff_load_string(client, SYS_CONTROL_PANEL , &s->control_panel, "gnome-control-center");
	aff_load_string(client, SYS_LOCK_SCREEN , &s->lock_screen, "gnome-screensaver-command --lock");
	aff_load_string(client, SYS_LOG_OUT , &s->log_out, "gnome-session-save --kill --gui");	
	aff_load_string(client, SYS_OPEN_URI , &s->open_uri, "gnome-open");	
	aff_load_string(client, SYS_FILE_MAN , &s->file_manager, "nautilus");	
	aff_load_string(client, SYS_COMPUTER , &s->computer, "Computer:///");	
	aff_load_string(client, SYS_NETWORK , &s->network, "Network:///");		

	
	/* filters */
	gconf_client_add_dir(client, FILT_PATH, GCONF_CLIENT_PRELOAD_NONE, NULL);
	aff_load_string(client, FILT_APPS , &s->apps, "apps");
	aff_load_string(client, FILT_BOOKS, &s->books, "books");
	aff_load_string(client, FILT_CONTACTS, &s->contacts, "contacts,people");
	aff_load_string(client, FILT_DOCS, &s->docs, "docs");		
	aff_load_string(client, FILT_EMAILS, &s->emails, "emails");
	aff_load_string(client, FILT_IMAGES, &s->images, "pics,images");
	aff_load_string(client, FILT_MUSIC, &s->music, "music,audio");
	aff_load_string(client, FILT_VIDS, &s->vids, "movies,vids");
		
			
	/* Appearence */
	gconf_client_add_dir(client, COL_PATH, GCONF_CLIENT_PRELOAD_NONE, NULL);
	aff_load_bool (client, COL_ROUNDED, &s->rounded_corners, FALSE);
	aff_load_color(client, COL_BACK_STEP_1, &s->back_step_1, "A1A8BBEC");
	aff_load_color(client, COL_BACK_STEP_2, &s->back_step_2, "141E3CF3");
	aff_load_color(client, COL_HIGH_STEP_1, &s->hi_step_1, "FFFFFF4E");
	aff_load_color(client, COL_HIGH_STEP_2, &s->hi_step_2, "FFFFFF55");

	aff_load_color(client, COL_HIGHLIGHT, &s->highlight, "FFFFFF28");
	aff_load_color(client, COL_BORDER, &s->border, "00151FE0");
	aff_load_color(client, COL_WIDGET_BORDER, &s->widget_border, "00000099");
	aff_load_color(client, COL_WIDGET_HIGHLIGHT, &s->widget_highlight, "FFFFFF50");	
	
	aff_load_string(client, COL_TEXT_COLOR, &s->text_color, "#ffffff");
	
	/* applet specific */
	gconf_client_add_dir(client, APPLET_PATH, GCONF_CLIENT_PRELOAD_NONE, NULL);
	aff_load_string(client, APPLET_ICON, &s->applet_icon, "gnome-main-menu");
	aff_load_string(client, APPLET_NAME, &s->applet_name, _("Computer"));	
	
	/* Make user dome directory */
	gchar *dir = NULL;
        const char *home = NULL;
        home = g_get_home_dir();
        if (home != NULL) {
		dir = g_strdup_printf("%s/.gnome2/affinity/actions", home);
	}
	if (dir != NULL) {
	        if (!g_file_test (dir, G_FILE_TEST_EXISTS))
	                g_mkdir_with_parents (dir, 0755);

	        g_free (dir);
	}
	
	return s;
}

AffSettings* 
aff_Settings_get_default (void)
{
        return settings;
}

GConfClient *
aff_settings_get_client (void)
{
	return client;
}

static void 
aff_notify_bool (GConfClient *client, guint cid, GConfEntry *entry, gboolean* data)
{
	GConfValue *value = NULL;
	
	value = gconf_entry_get_value(entry);
	*data = gconf_value_get_bool(value);
	
	if (*data)
		g_print("%s is true\n", gconf_entry_get_key(entry));
}

static void 
aff_notify_string (GConfClient *client, guint cid, GConfEntry *entry, gchar** data)
{
	GConfValue *value = NULL;
	
	value = gconf_entry_get_value(entry);
	*data = (gchar *) gconf_value_get_string(value);
	
	//g_print("%s is %s\n", gconf_entry_get_key(entry), *data);
}

static void 
aff_notify_float (GConfClient *client, guint cid, GConfEntry *entry, gfloat* data)
{
	GConfValue *value = NULL;
	
	value = gconf_entry_get_value(entry);
	*data = gconf_value_get_float(value);
	//g_print("%s is %f\n", gconf_entry_get_key(entry), *data);
}

static void 
aff_notify_int (GConfClient *client, guint cid, GConfEntry *entry, int* data)
{
	GConfValue *value = NULL;
	
	value = gconf_entry_get_value(entry);
	*data = gconf_value_get_int(value);
	//g_print("%s is %f\n", gconf_entry_get_key(entry), *data);
}

static void 
aff_notify_color (GConfClient *client, guint cid, GConfEntry *entry, AffColor* color)
{
	GConfValue *value = NULL;
	float colors[4];
	
	value = gconf_entry_get_value(entry);
	hex2float( (gchar *)gconf_value_get_string(value), colors);
	
	color->red = colors[0];
	color->green = colors[1];
	color->blue = colors[2];
	color->alpha = colors[3];
}


static void
aff_load_bool(GConfClient *client, const gchar* key, gboolean *data, gboolean def)
{
	GConfValue *value = NULL;
	
	value = gconf_client_get(client, key, NULL);
	if (value) {
		*data = gconf_client_get_bool(client, key, NULL);
	} else {
		g_print("%s unset, setting now\n", key);
		gconf_client_set_bool (client, key, def, NULL);
		*data = def;
	}
	gconf_client_notify_add (client, key, (GConfClientNotifyFunc)aff_notify_bool, data, NULL, NULL);
}

static void
aff_load_string(GConfClient *client, const gchar* key, gchar **data, const char *def)
{
	GConfValue *value = NULL;
	
	value = gconf_client_get(client, key, NULL);
	if (value) {
		*data = gconf_client_get_string(client, key, NULL);
	} else {
		g_print("%s unset, setting now\n", key);
		gconf_client_set_string (client, key, def, NULL);
		*data = g_strdup(def);
	}
	
	gconf_client_notify_add (client, key, (GConfClientNotifyFunc)aff_notify_string, data, NULL, NULL);
}

static void
aff_load_float(GConfClient *client, const gchar* key, gfloat *data, float def)
{
	GConfValue *value = NULL;
	
	value = gconf_client_get(client, key, NULL);
	if (value) {
		*data = gconf_client_get_float(client, key, NULL);
	} else {
		g_print("%s unset, setting now\n", key);
		gconf_client_set_float (client, key, def, NULL);
		*data = def;
	}
	
	gconf_client_notify_add (client, key, (GConfClientNotifyFunc)aff_notify_float, data, NULL, NULL);
}

static void
aff_load_int(GConfClient *client, const gchar* key, int *data, int def)
{
	GConfValue *value = NULL;
	
	value = gconf_client_get(client, key, NULL);
	if (value) {
		*data = gconf_client_get_int(client, key, NULL);
	} else {
		g_print("%s unset, setting now\n", key);
		gconf_client_set_int (client, key, def, NULL);
		*data = def;
	}
	
	gconf_client_notify_add (client, key, (GConfClientNotifyFunc)aff_notify_int, data, NULL, NULL);
}

static void
aff_load_color(GConfClient *client, const gchar* key, AffColor *color, const char * def)
{
	float colors[4];
	GConfValue *value = NULL;
	
	value = gconf_client_get(client, key, NULL);
	if (value) {
		hex2float (gconf_client_get_string(client, key, NULL), colors);
		color->red = colors[0];
		color->green = colors[1];
		color->blue = colors[2];
		color->alpha = colors[3];
	} else {
		g_print("%s unset, setting now\n", key);
		gconf_client_set_string (client, key, def, NULL);
		hex2float ( (gchar*)def, colors);
		color->red = colors[0];
		color->green = colors[1];
		color->blue = colors[2];
		color->alpha = colors[3];
	}
		
	gconf_client_notify_add (client, key, (GConfClientNotifyFunc)aff_notify_color, color, NULL, NULL);
}

static void
aff_load_string_list(GConfClient *client, const gchar* key, GSList **data, GSList *def)
{
	GConfValue *value = NULL;
	//GSList *slist = def;
	
	value = gconf_client_get(client, key, NULL);
	if (value) {
		*data = gconf_client_get_list ( client, key, GCONF_VALUE_STRING, NULL);
	} else {
		g_print("%s unset, setting now\n", key);
		gconf_client_set_list (client, key, GCONF_VALUE_STRING, NULL, NULL);
		*data = NULL;
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

