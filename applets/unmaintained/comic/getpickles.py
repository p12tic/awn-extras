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
# get_bornloser_strips.py -- fetch strips of last N days

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

pattern  = re.compile('str_strip[0-9/]+\\.full\\.gif')
pattern2 = re.compile('str_strip[0-9/]+\\.full\\.jpg')
temp1 = 'http://www.comics.com/pickles/%s/'
temp2 = 'http://assets.comics.com/dyn/%s'

date = datetime.today()
one_day = timedelta(1)

filename = None

for i in range(number_of_days):
    url = temp1 % (date.strftime('%Y-%m-%d'))
    #print '? %s' % (url)
    fil = urllib.urlopen(url)
    for line in fil:
        match = pattern.search(line)
        if match != None:
            filename = match.group()
            break
    	else:
	    match2 = pattern2.search(line)
	    if match2 != None:
	        filename = match2.group()
                break
    fil.close()

    if filename != None:
        url = temp2 % (filename)
        #print '+ %s' % (url)
        fil = urllib.urlopen(url)
        diskfile = file(path_prefix + 'dilbert.gif', 'w')
        diskfile.write(fil.read())
        fil.close()
        diskfile.close()

    date = date - one_day
    filename = None
