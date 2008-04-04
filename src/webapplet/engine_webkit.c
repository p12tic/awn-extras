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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#ifdef HAVE_OLD_WEBKITGTK
#include <webkitwebview.h>
#else
#include <webkit/webkitwebview.h>
#endif

#include  "engine_webkit.h"
#include  "engine_html.h"

void
wrapper_webkit_init_engine (FunctionList *function_list)
{
  function_list->_html_web_view_open = (html_web_view_open_fn)webkit_web_view_open;
  function_list->_html_web_view_new = webkit_web_view_new;
}
/* vim: set et ts=2 sts=2 sw=2 : */
