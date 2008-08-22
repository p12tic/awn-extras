#!/usr/bin/python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

################################################################
# getxkcd.py -- fetch last (current) xkcd strip

################################################################
# BEGIN configuration


path_prefix = '/tmp/' # where do you want to save the files?

# --END configuration
################################################################

import urllib
import re


comic = urllib.urlopen("http://www.xkcd.com/")
link = re.compile("http://imgs.xkcd.com/comics/.*png").search(comic.read(),1)
fil = urllib.urlopen(link.group())

diskfile = file(path_prefix + 'dilbert.gif', 'w')
diskfile.write(fil.read())
fil.close()
diskfile.close()

