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
 
#ifndef AFF_SEARCH_ENGINE_ACTIONS_H
#define AFF_SEARCH_ENGINE_ACTIONS_H

#include "aff-search-engine.h"

#define AFF_TYPE_SEARCH_ENGINE_ACTIONS		(aff_search_engine_actions_get_type ())
#define AFF_SEARCH_ENGINE_ACTIONS(obj)		(G_TYPE_CHECK_INSTANCE_CAST ((obj), AFF_TYPE_SEARCH_ENGINE_ACTIONS, AffSearchEngineActions))
#define AFF_SEARCH_ENGINE_ACTIONS_CLASS(klass)	(G_TYPE_CHECK_CLASS_CAST ((klass), AFF_TYPE_SEARCH_ENGINE_ACTIONS, AffSearchEngineActionsClass))
#define AFF_IS_SEARCH_ENGINE_ACTIONS(obj)		(G_TYPE_CHECK_INSTANCE_TYPE ((obj), AFF_TYPE_SEARCH_ENGINE_ACTIONS))
#define AFF_IS_SEARCH_ENGINE_ACTIONS_CLASS(klass)	(G_TYPE_CHECK_CLASS_TYPE ((klass), AFF_TYPE_SEARCH_ENGINE_ACTIONS))
#define AFF_SEARCH_ENGINE_ACTIONS_GET_CLASS(obj)   (G_TYPE_INSTANCE_GET_CLASS ((obj), AFF_TYPE_SEARCH_ENGINE_ACTIONS, AffSearchEngineActionsClass))

typedef struct AffSearchEngineActionsDetails AffSearchEngineActionsDetails;

typedef struct AffSearchEngineActions {
	AffSearchEngine parent;
	AffSearchEngineActionsDetails *details;
} AffSearchEngineActions;

typedef struct {
	AffSearchEngineClass parent_class;
} AffSearchEngineActionsClass;

GType aff_search_engine_actions_get_type (void);

AffSearchEngine* aff_search_engine_actions_new (void);

#endif /* AFF_SEARCH_ENGINE_ACTIONS_H */
