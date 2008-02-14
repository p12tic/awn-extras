/* -*- Mode: C; tab-width: 8; indent-tabs-mode: t; c-basic-offset: 8 -*- */
/*
 * Copyright (C) 2007 Neil J. Patel <njpatel@gmail.com>
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
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 * Authors: Neil J. Patel <njpatel@gmail.com> 
 *
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "aff-search-engine.h"


static void  aff_search_engine_class_init       (AffSearchEngineClass *class);
static void  aff_search_engine_init             (AffSearchEngine      *engine);

G_DEFINE_ABSTRACT_TYPE (AffSearchEngine,
			aff_search_engine,
			G_TYPE_OBJECT);

static GObjectClass *parent_class = NULL;

static void
finalize (GObject *object)
{
	AffSearchEngine *engine;

	engine = AFF_SEARCH_ENGINE (object);
	
	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(object);
}

static void
aff_search_engine_class_init (AffSearchEngineClass *class)
{
	GObjectClass *gobject_class;

	parent_class = g_type_class_peek_parent (class);

	gobject_class = G_OBJECT_CLASS (class);
	gobject_class->finalize = finalize;

}

static void
aff_search_engine_init (AffSearchEngine *engine)
{
}

AffSearchEngine *
aff_search_engine_new (void)
{
	AffSearchEngine *engine;

	engine = g_object_new(AFF_TYPE_SEARCH_ENGINE, 
					  NULL);
	return engine;
}

void
aff_search_engine_set_query (AffSearchEngine *engine, AffResults *results, gulong id, const gchar *query, AffQueryType type)
{
	g_return_if_fail (AFF_IS_SEARCH_ENGINE (engine));
	g_return_if_fail (AFF_SEARCH_ENGINE_GET_CLASS (engine)->set_query != NULL);

	AFF_SEARCH_ENGINE_GET_CLASS (engine)->set_query (engine, results, id, query, type);
}
