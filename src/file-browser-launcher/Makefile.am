APPLET_NAME = file-browser-launcher
APPLET_MAIN_FILE = file-browser-launcher.py

include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA =			\
	about.py			\
	file-browser-launcher.py	\
	prefs.py			\
	gconfwrapper.py			\
	$(NULL)

fbl_iconsdir = $(applet_datadir)/icons
dist_fbl_icons_DATA =	\
	icons/folder.png\
	$(NULL)
