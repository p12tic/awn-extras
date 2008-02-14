#!/usr/bin/python
################################################################
# getxkcd.py -- fetch last (current) xkcd strip

################################################################
# BEGIN configuration


path_prefix = './' # where do you want to save the files?

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

