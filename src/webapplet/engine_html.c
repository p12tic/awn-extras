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
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
*/

#define HAVE_WEBKIT
#undef  HAVE_MOZ

#include <gtk/gtk.h>

#ifdef HAVE_WEBKIT  
#include "engine_webkit.h"
#endif

#include "engine_html.h"

static  engine=ENGINE_WEBKIT;

static  FunctionList  function_list;  

void html_init()
{
  switch(engine)
  {
#ifdef HAVE_WEBKIT    
    case  ENGINE_WEBKIT:
      wrapper_webkit_init_engine(&function_list);
      break;
#endif      
  }
}  

void html_web_view_open(GtkWidget * viewer,const gchar * uri)
{
  function_list._html_web_view_open(viewer,uri);
}  

GtkWidget * html_web_view_new(void)
{
  return function_list._html_web_view_new();
}  
