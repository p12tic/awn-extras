# vim: set ts=8 sts=8 sw=8 :
SUBDIRS = locale
		
APPLET_NAME = comics
APPLET_MAIN_FILE = comics.py
include $(top_srcdir)/Makefile.python-applet

dist_applet_DATA =	\
	comics.sh       \
	comics.pot	\
	comics_add.py	\
	comics_manage.py\
	comics_view.py	\
	COPYING		\
	downloader.py	\
	main.py	        \
	shared.py	\
	sv_SE.po	\
	widgets.py	\
	$(NULL)

feeddir = $(applet_datadir)/feed
dist_feed_DATA =		\
	feed/__init__.py	\
	feed/basic.py		\
	feed/rss.py		\
	feed/settings.py	\
	$(NULL)

feedsdir = $(applet_datadir)/feeds
dist_feeds_DATA = $(wildcard feeds/*.feed)

gladedir = $(applet_datadir)/glade
dist_glade_DATA =		\
	glade/add.glade		\
	glade/comics.svg	\
	glade/logo.svg		\
	glade/main.glade	\
	glade/manage.glade	\
	glade/manage.svg	\
	glade/view.glade	\
	$(NULL)

custom_icondir = $(applet_datadir)/icons
dist_custom_icon_DATA =		\
	icons/comics-icon.svg	\
	icons/default.svg	\
	icons/error.svg		\
	$(NULL)
