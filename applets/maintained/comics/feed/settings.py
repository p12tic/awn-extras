# -*- coding: utf-8 -*-

# Copyright (c) 2008 Moses Palmér
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os


class Settings(dict):
    """A class to save and store settings."""

    COMMENT_CHAR = '#'
    COLS = 80

    def trim(self, s):
        return ' '.join(s.split())

    def separate(self, s):
        return s.split()

    def escape(self, s):
        return s

    def unescape(self, s):
        return s

    def make_comment(self, s):
        """Turn s into a single line comment."""
        return ' '.join([self.COMMENT_CHAR, self.trim(s)])

    def make_comment_span(self, s):
        """Return a list of lines."""
        words = self.separate(s)
        result = []
        current = self.COMMENT_CHAR

        for word in words:
            if len(current) + len(word) + 1 > self.COLS:
                result.append(current)
                current = self.COMMENT_CHAR
            current = ' '.join([current, word])

        if len(current) > len(self.COMMENT_CHAR):
            result.append(current)

        return result

    def __init__(self, filename=None):
        """Open filename and read its settings."""
        self.description = None
        self.filename = filename
        self.basename = None
        self.comments = {}

        if filename:
            self.basename = os.path.basename(filename).split('.', 1)[0]
            # Read contents of settings file
            try:
                f = open(self.filename)
                data = f.readlines()
                f.close()

                reading_description = True
                current_comment = None

                # Parse file
                for line in data:
                    item_comment = line.split('#', 1)
                    key_val = item_comment[0].split('=', 1)
                    key = self.trim(key_val[0])

                    # Are we reading the description of the file?
                    if reading_description:
                        if len(key_val) == 2:
                            reading_description = False
                        elif len(self.trim(line)) == 0:
                            self.description = current_comment
                            reading_description = False
                            current_comment = None

                    # Did this line contain a comment?
                    if len(item_comment) == 2:
                        comment = item_comment[1]
                        if len(key) > 0 or current_comment is None:
                            current_comment = comment
                        else:
                            current_comment = ' '.join([current_comment,
                                comment])

                    # Is this a key-value pair?
                    if len(key_val) == 2:
                        value = key_val[1][:-1]

                        self[key] = self.unescape(value)
                        if current_comment:
                            self.comments[key] = self.trim(current_comment)

            except IOError:
                pass

    def save(self):
        """Write the settings to the file."""
        if self.filename:
            f = open(self.filename, 'w')

            if self.description:
                for l in self.make_comment_span(self.description):
                    f.write(l)
                    f.write('\n')
                f.write('\n')

            for key, value in self.items():
                if key in self.comments:
                    comment = self.make_comment_span(self.comments[key])
                else:
                    comment = []

                key_val = '='.join((key, str(value)))

                for l in comment:
                    f.write(l)
                    f.write('\n')
                f.write(key_val)
                f.write('\n')

            f.close()

    def delete(self):
        """Removes the file."""
        if self.filename:
            try:
                os.remove(self.filename)
                return True
            except Exception:
                return False

    def get_string(self, name, default=None):
        """Read a string setting."""
        if name in self:
            return self[name]
        elif not default is None:
            return default
        else:
            raise KeyError()

    def get_bool(self, name, default=None):
        """Read a boolean setting."""
        if name in self:
            val = self[name]
            if val == 'True':
                return True
            elif val == 'False':
                return False
        elif not default is None:
            return default
        else:
            raise KeyError()

    def get_int(self, name, default=None):
        """Read an integer setting."""
        if name in self:
            try:
                return int(self[name])
            except ValueError:
                pass
        elif not default is None:
            return default
        else:
            raise KeyError()

    def remove(self, key):
        """Remove the key."""
        if key in self:
            del self[key]
