/***************************************************************************
 *            config_shared.c
 *
 *  Thu Apr 24 13:35:30 2008
 *  Copyright  2008  Rodney Cryderman <rcryderman@gmail.com>
 *  
 ****************************************************************************/

/*
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
 
#include <libawn/awn-config-client.h>

AwnConfigClient * get_conf(void)
{
    static AwnConfigClient		*config=NULL;
    if (!config)    
    {
        config = awn_config_client_new_for_applet ("shared", NULL);
    }
    return config;
}        

gboolean share_config_bool(const gchar * key)
{
    return awn_config_client_get_bool(get_conf(), AWN_CONFIG_CLIENT_DEFAULT_GROUP, key, NULL);	
}

