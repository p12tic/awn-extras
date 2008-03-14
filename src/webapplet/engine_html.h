/*
 * Copyright (c) 2008   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
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
#ifndef __ENGINE_HTML_H
 
#define __ENGINE_HTML_H

#include <gtk/gtk.h>

enum
{
  ENGINE_WEBKIT   
};

typedef void (*html_web_view_open_fn)(GtkWidget * viewer,const gchar * uri);
typedef GtkWidget * (*html_web_view_new_fn)(void);

typedef struct
{
      html_web_view_open_fn   _html_web_view_open;
      html_web_view_new_fn    _html_web_view_new;
  
}FunctionList;  

void html_web_view_open(GtkWidget * viewer,const gchar * uri);
GtkWidget * html_web_view_new(void);

#endif
