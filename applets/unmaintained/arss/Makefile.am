APPLET_NAME = arss
APPLET_MAIN_FILE = arss.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA =		\
	adddialog.glade 	\
	arssconfig.py		\
	feedparserdb.py		\
	arss.py			\
	menus.py		\
	configwindow.glade	\
	$(NULL)

arss_iconsdir = $(applet_datadir)/icons
dist_arss_icons_DATA =			\
	icons/feed-icon-gray.svg	\
	icons/feed-icon-read.png	\
	icons/feed-icon.svg		\
	icons/feed-icon-unread.png	\
	$(NULL)
