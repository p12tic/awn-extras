APPLET_NAME = gwibfawn
APPLET_MAIN_FILE = gwibfawn.py
include $(top_srcdir)/Makefile.python-applet

dist_applet_DATA =			\
	COPYING				\
	$(NULL)
#	media-player-prefs.glade

microblogdir = $(applet_datadir)/microblog
dist_microblog_DATA = $(wildcard microblog/*.py)

supportdir = $(applet_datadir)/microblog/support
dist_support_DATA = $(wildcard microblog/support/*.py)

#mp_iconsdir = $(applet_datadir)/icons
#dist_mp_icons_DATA =		\
#	icons/COPYING		\
#	icons/README		\
#	icons/media-player.png	\
#	$(NULL)
