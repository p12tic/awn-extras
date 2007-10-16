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

#ifndef __FILEBROWSER_DEFINES_H__
#define __FILEBROWSER_DEFINES_H__

#define FILEBROWSER_TEXT_SELECT_FOLDER "Select folder as item container"
#define FILEBROWSER_TEXT_OPEN_FILEMANAGER "Open filemanager"

#define DIALOG_CONTROLS_HEIGHT 30
#define ICON_MARGIN_X 12
#define ICON_MARGIN_Y ICON_MARGIN_X
#define ICON_NAME_MARGIN 6
#define ICON_NAME_HEIGHT 24
#define FILEBROWSER_ICON_RECT_RADIUS 20
#define MIN_WIDTH 200
#define MIN_HEIGHT 200
#define PADDING 1

#define DRAG_ACTION_LINK "link"
#define DRAG_ACTION_COPY "copy"
#define DRAG_ACTION_MOVE "move"
#define DRAG_ACTION_SYSTEM "system"

#define FILEBROWSER_DEFAULT_MAX_ROWS 4
#define FILEBROWSER_DEFAULT_MAX_COLS 5
#define FILEBROWSER_DEFAULT_SHOW_FILES TRUE
#define FILEBROWSER_DEFAULT_SHOW_HIDDEN_FILES FALSE
#define FILEBROWSER_DEFAULT_SHOW_FOLDERS TRUE
#define FILEBROWSER_DEFAULT_SHOW_DESKTOP_ITEMS TRUE
#define FILEBROWSER_DEFAULT_DEFAULT_DRAG_ACTION DRAG_ACTION_LINK
#define FILEBROWSER_DEFAULT_ENABLE_BROWSING TRUE
#define FILEBROWSER_DEFAULT_COMPOSITE_APPLET_ICON TRUE
#define FILEBROWSER_DEFAULT_APPLET_ICON "folder-drag-accept"
#define FILEBROWSER_DEFAULT_ICON_SIZE 64

#define FILEBROWSER_GCONFKEY_MAX_ROWS "maximum_rows"
#define FILEBROWSER_GCONFKEY_MAX_COLS "maximum_cols"
#define FILEBROWSER_GCONFKEY_SHOW_FILES "show_files"
#define FILEBROWSER_GCONFKEY_SHOW_HIDDEN_FILES "show_hidden_files"
#define FILEBROWSER_GCONFKEY_SHOW_FOLDERS "show_folders"
#define FILEBROWSER_GCONFKEY_SHOW_DESKTOP_ITEMS "show_desktop_items"
#define FILEBROWSER_GCONFKEY_DEFAULT_DRAG_ACTION "default_drag_action"
#define FILEBROWSER_GCONFKEY_ENABLE_BROWSING "enable_browsing"
#define FILEBROWSER_GCONFKEY_COMPOSITE_APPLET_ICON "enable_composite_applet_icon"
#define FILEBROWSER_GCONFKEY_BACKEND_FOLDER "backend_folder"
#define FILEBROWSER_GCONFKEY_APPLET_ICON "applet_icon"
#define FILEBROWSER_GCONFKEY_ICON_SIZE "icon_size"

#endif /* __FILEBROWSER_DEFINES_H__ */

