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
# getgarfield.py -- fetch strips of last N days

################################################################
# BEGIN configuration

number_of_days = 1

path_prefix = '/tmp/' # where do you want to save the files?

# --END configuration
################################################################

import sys
import urllib
import re

from string import join
from datetime import datetime, timedelta

if len(sys.argv) > 1:
    number_of_days = int(sys.argv[1])

temp = 'http://picayune.uclick.com/comics/ga/%s/ga%s.%s'

date = datetime.today()
one_day = timedelta(1)

for i in range(number_of_days):

    giforjpg = 'gif'
      
    url = temp % (date.strftime('%Y'),date.strftime('%y%m%d'),giforjpg)
    print '+ %s' % (url)
    fil = urllib.urlopen(url)
    diskfile = file(path_prefix + 'dilbert.gif', 'w')
    diskfile.write(fil.read())
    fil.close()
    diskfile.close()

    date = date - one_day
