#!/usr/bin/python
################################################################
# get_wizofid_strips.py -- fetch wizofids strips of last N days

################################################################
# BEGIN configuration

number_of_days = 1

path_prefix = './' # where do you want to save the files?

# --END configuration
################################################################

import sys
import urllib
import re

from string import join
from datetime import datetime, timedelta

if len(sys.argv) > 1:
    number_of_days = int(sys.argv[1])

pattern = re.compile('wizardofid\\d+\\.gif')
pattern2 = re.compile('wizardofid\\d+\\.jpg')
temp1 = 'http://www.comics.com/creators/wizardofid/archive/wizardofid-%s.html'
temp2 = 'http://www.comics.com/creators/wizardofid/archive/images/%s'

date = datetime.today()
one_day = timedelta(1)

filename = None

for i in range(number_of_days):
    url = temp1 % (date.strftime('%Y%m%d'))
    print '? %s' % (url)
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
        print '+ %s' % (url)
        fil = urllib.urlopen(url)
        diskfile = file(path_prefix + 'dilbert.gif', 'w')
        diskfile.write(fil.read())
        fil.close()
        diskfile.close()

    date = date - one_day
    filename = None
