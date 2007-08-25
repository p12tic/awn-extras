/*
 * Copyright (c) 2007 Timon David Ter Braak
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

#ifndef __STACK_DEFINES_H__
#define __STACK_DEFINES_H__

#define STACK_TEXT_SELECT_FOLDER "Select folder as item container"
#define STACK_TEXT_OPEN_FILEMANAGER "Open filemanager"

#define DIALOG_CONTROLS_HEIGHT 30
#define ICON_MARGIN_X 12
#define ICON_MARGIN_Y ICON_MARGIN_X
#define ICON_NAME_MARGIN 6
#define ICON_NAME_HEIGHT 24
#define STACK_ICON_RECT_RADIUS 10
#define MIN_WIDTH 200
#define MIN_HEIGHT 200
#define PADDING 1

#define DRAG_ACTION_LINK "link"
#define DRAG_ACTION_COPY "copy"
#define DRAG_ACTION_MOVE "move"

#define STACK_DEFAULT_MAX_ROWS 4
#define STACK_DEFAULT_MAX_COLS 5
#define STACK_DEFAULT_SHOW_FILES TRUE
#define STACK_DEFAULT_SHOW_HIDDEN_FILES FALSE
#define STACK_DEFAULT_SHOW_FOLDERS TRUE
#define STACK_DEFAULT_SHOW_DESKTOP_ITEMS TRUE
#define STACK_DEFAULT_DEFAULT_DRAG_ACTION DRAG_ACTION_LINK
#define STACK_DEFAULT_ENABLE_BROWSING TRUE
#define STACK_DEFAULT_COMPOSITE_APPLET_ICON TRUE
#define STACK_DEFAULT_APPLET_ICON "folder-drag-accept"
#define STACK_DEFAULT_ICON_SIZE 64
#define STACK_DEFAULT_BORDER_COLOR "FFFFFFFF"
#define STACK_DEFAULT_BACKGROUND_COLOR "000000AA"
#define STACK_DEFAULT_ICONTEXT_COLOR "FFFFFFFF"

#define STACK_GCONFKEY_MAX_ROWS "maximum_rows"
#define STACK_GCONFKEY_MAX_COLS "maximum_cols"
#define STACK_GCONFKEY_SHOW_FILES "show_files"
#define STACK_GCONFKEY_SHOW_HIDDEN_FILES "show_hidden_files"
#define STACK_GCONFKEY_SHOW_FOLDERS "show_folders"
#define STACK_GCONFKEY_SHOW_DESKTOP_ITEMS "show_desktop_items"
#define STACK_GCONFKEY_DEFAULT_DRAG_ACTION "default_drag_action"
#define STACK_GCONFKEY_ENABLE_BROWSING "enable_browsing"
#define STACK_GCONFKEY_COMPOSITE_APPLET_ICON "enable_composite_applet_icon"
#define STACK_GCONFKEY_BACKEND_FOLDER "backend_folder"
#define STACK_GCONFKEY_APPLET_ICON "applet_icon"
#define STACK_GCONFKEY_ICON_SIZE "icon_size"
#define STACK_GCONFKEY_BORDER_COLOR "border_color"
#define STACK_GCONFKEY_BACKGROUND_COLOR "background_color"
#define STACK_GCONFKEY_ICONTEXT_COLOR "icontext_color"

enum {
    DIR_DOWN = 0,
    DIR_UP = 1,
    DIR_LEFT = 2,
    DIR_RIGHT = 3
};

#endif /* __STACK_DEFINES_H__ */
