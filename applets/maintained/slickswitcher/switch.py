#!/usr/bin/env python
#
# Copyright (c) 2010 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import wnck
#To make code a tiny bit cleaner
x, y, w, h, name = range(5)

class Switch:
    connected_functions = []

    def __init__(self):
        #Get the screen
        self.screen = wnck.screen_get_default()
        self.screen.force_update()
        self.active_workspace = self.screen.get_active_workspace()
        print "active workspace:", self.active_workspace

        #Get screen width and height
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()

        #Connect to signals from Wnck
        self.screen.connect('active-window-changed', self.emitted)
        self.screen.connect('active-workspace-changed', self.workspace_changed)
        self.screen.connect('window-manager-changed', self.emitted)
        self.screen.connect('window-stacking-changed', self.emitted)
        self.screen.connect('viewports-changed', self.emitted)

    #Connect to any events from Wnck
    def connect(self, func):
        self.connected_functions.append(func)

    #A signal from Wnck was emitted
    def emitted(self, *args):
        for func in self.connected_functions:
            func()

    def workspace_changed(self, *args):
        self.active_workspace = self.screen.get_active_workspace()
        if self.active_workspace == None: print "AAAAAAAAAAAAAA"
        self.emitted()

    #Return the number of columns
    def get_num_columns(self, current_workspace=None):
        #Get the active workspace if necessary
        if current_workspace is None:
            current_workspace = self.active_workspace

        #Get the workspace width
        workspace_width = current_workspace.get_width()

        #Return the number of columns
        num = workspace_width / self.width
        if num <= 0:
            return 1
        else:
            return num

    #Return the number of rows
    def get_num_rows(self, current_workspace=None):
        #Get the active workspace if necessary
        if current_workspace is None:
            current_workspace = self.active_workspace

        #Get the workspace height
        workspace_height = current_workspace.get_height()

        #Return the number of columns
        num = workspace_height / self.height
        if num <= 0:
            return 1
        else:
            return num

    #Return the number of the current workspace
    def get_current_workspace_num(self, current_workspace=None):
        #Get the active workspace if necessary
        if current_workspace is None:
            current_workspace = self.active_workspace

        if not current_workspace.is_virtual():
            return current_workspace.get_number() + 1

        #Get the workspace dimensions
        workspace_width = current_workspace.get_width()
        workspace_height = current_workspace.get_height()

        #Get the workspace's position (x & y)
        workspace_x = current_workspace.get_viewport_x()
        workspace_y = current_workspace.get_viewport_y()

        #Get the number of columns
        num_columns = self.get_num_columns(current_workspace)

        #Get the current column and current row
        current_column = workspace_x / self.width
        current_row = workspace_y / self.height

        #Put all this together to get the current workspace number
        return current_row * num_columns + current_column + 1

    #Move, either forward or backwards
    def move(self, direction):
        #Get the current workspace
        current_workspace = self.screen.get_active_workspace()

        if current_workspace is None:
            return

        #Get the number of the current workspace
        current_workspace_num = self.get_current_workspace_num(current_workspace)

        #Get the number of columns and rows
        num_columns = self.get_num_columns(current_workspace)
        num_rows = self.get_num_rows(current_workspace)

        #If moving forward
        if direction == True:
            #If this is not the last workspace, go to the next one
            if current_workspace_num != num_columns * num_rows:
                move_to = current_workspace_num + 1
            #Otherwise, go to the first
            else:
                move_to = 1

            #Find out to which row and column to move
            move_to_row = (move_to - 1) / num_columns
            move_to_column = move_to - num_columns * move_to_row - 1

        #Moving backwards
        elif direction == False:
            #If this is noe the first workspace, go to the previous one
            if current_workspace_num != 1:
                move_to = current_workspace_num - 1
            #Otherwise, go to the last
            else:
                move_to = num_columns * num_rows

            #Find out to which row and column to move
            move_to_row = (move_to - 1) / num_columns
            move_to_column = move_to - num_columns * move_to_row - 1

        #Moving to a specific viewport
        else:
            move_to_row, move_to_column = direction[0], direction[1]

        #Move
        self.screen.move_viewport(self.width * move_to_column, \
            self.height * move_to_row)

    #Return the list of windows
    def get_windows(self, for_workspace=-1):
        #Get the list of windows
        windows = self.screen.get_windows_stacked()

        #List of windows' position and size
        windows_pos_size = []

        #List of sticky windows
        sticky_windows = []

        #Get the number of the current workspace
        current_workspace = self.get_current_workspace_num()

        #Get the number of columns and rows
        num_columns = self.get_num_columns()
        num_rows = self.get_num_rows()

        #Get the row and column which the user is currently in
        current_row = int((current_workspace-1) / float(num_columns)) + 1
        current_column = int((current_workspace-1) % num_columns) + 1

        #Go through each window
        for window in windows:

            #Don't include the window if it's minimized or skipping the pager
            if not window.is_minimized() and not window.is_skip_pager():

                #Check if the window is sticky
                if window.is_sticky():

                    #Append it to the list of sticky windows
                    w_x, w_y, width, height = window.get_geometry()
                    sticky_windows.append([w_x, w_y, width, height, window.get_name()])

                #The window is not sticky
                else:

                    #Get the window's position and size
                    w_x, w_y, width, height = window.get_geometry()
                    windows_pos_size.append([w_x, w_y, width, height, window.get_name()])

        #Check if we should return windows from every workspace
        if for_workspace == -1:

            #Make a list of lists of windows
            workspaces = []

            #Go through each workspace
            for workspace in range(num_columns * num_rows):
                workspaces.append([])

                #Go through each sticky window
                for window in stick_windows:

                    #Append to the list
                    workspaces[workspace].append(window)

                #Go through each suitable window
                for window in windows_pos_size:

                    #If this is the current workspace
                    if workspace + 1 == current_workspace:

                        #Check if the window is not off the screen (same workspace)
                        if not (window[x] < 0 or window[x] >= self.width or \
                            window[y] < 0 or window[y] >= self.height):

                            workspaces[workspace].append(window)

                    #Not the current workspace
                    else:
                        tmp_window = [window[x], window[y], window[w], window[h], window[4]]

                        #Get the row and column which this workspace is in
                        row = int((workspace) / float(num_columns)) + 1
                        column = int((workspace) % num_columns) + 1

                        #Now we must find out if this window is in this iterated workspace
                        #The window's position is determined relative
                        #to the current workspace

                        #If this workspace is not in the same column as the current one
                        if column < current_column:
                            tmp_window[x] = window[x]+self.width*(current_column-column)
                        elif column > current_column:
                            tmp_window[x] = window[x]-self.width*(column-current_column)

                        #If this workspace is not in the same row as the current one
                        if row < current_row:
                            tmp_window[y] = window[y]+self.height*(current_row-row)
                        elif row > current_row:
                            tmp_window[y] = window[y]-self.height*(row-current_row)

                        #Now we find out if this window is on this workspace
                        if not (tmp_window[x] < 0 or tmp_window[x] >= self.width or \
                            tmp_window[y] < 0 or tmp_window[y] >= self.height):

                            #It is; add it to the list of windows for this workspace
                            workspaces[workspace].append(tmp_window)

                            #Remove it from the list of windows to save a tiny bit
                            #of processing power
                            windows_pos_size.remove(window)

        #Return the list of windows for one specific viewport
        else:
            #Make a list of windows
            windows = []

            #Go through each sticky window
            for window in sticky_windows:

                #Append it to the list
                windows.append(window)

            #Go through each suitable window
            for window in windows_pos_size:

                #If this is the current workspace
                if for_workspace + 1 == current_workspace:

                    #Check if the window is not off the screen (same workspace)
                    if not (window[x] < 0 or window[x] >= self.width or \
                        window[y] < 0 or window[y] >= self.height):

                        windows.append(window)

                #Not the current workspace
                else:
                    tmp_window = [window[x], window[y], window[w], window[h], window[4]]

                    #Get the row and column which this workspace is in
                    row = int((for_workspace) / float(num_columns)) + 1
                    column = int((for_workspace) % num_columns) + 1

                    #Now we must find out if this window is in this iterated workspace
                    #The window's position is determined relative
                    #to the current workspace

                    #If this workspace is not in the same column as the current one
                    if column < current_column:
                        tmp_window[x] = window[x]+self.width*(current_column-column)
                    elif column > current_column:
                        tmp_window[x] = window[x]-self.width*(column-current_column)

                    #If this workspace is not in the same row as the current one
                    if row < current_row:
                        tmp_window[y] = window[y]+self.height*(current_row-row)
                    elif row > current_row:
                        tmp_window[y] = window[y]-self.height*(row-current_row)

                    #Now we find out if this window is on this workspace
                    if not (tmp_window[x] < 0 or tmp_window[x] >= self.width or \
                        tmp_window[y] < 0 or tmp_window[y] >= self.height):

                        #It is; add it to the list of windows for this workspace
                        windows.append(tmp_window)

                        #Remove it from the list of windows to save a tiny bit
                        #of processing power
                        windows_pos_size.remove(window)

            #Return the list of windows
            return windows

        #Return the list of workspaces and their respective windows
        return workspaces
