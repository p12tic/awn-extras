# vim: set ts=8 sts=8 sw=8 :
APPLET_NAME = comics
APPLET_MAIN_FILE = comics.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA = \
	comics.sh \
	comics_add.py \
	comics_manage.py \
	comics_view.py \
	COPYING \
	downloader.py \
	main.py \
	shared.py \
	widgets.py \
	$(NULL)

feeddir = $(applet_datadir)/feed
dist_feed_DATA = \
	feed/__init__.py \
	feed/basic.py \
	feed/rss.py \
	feed/settings.py \
	$(NULL)

feedsdir = $(applet_datadir)/feeds
dist_feeds_DATA = $(wildcard feeds/*.feed)

pluginsdir = $(applet_datadir)/feed/plugins
dist_plugins_DATA = $(wildcard feed/plugins/*.py)

uidir = $(applet_datadir)/ui
dist_ui_DATA = \
	$(wildcard ui/*.svg) \
	$(wildcard ui/*.ui) \
	$(NULL)

custom_icondir = $(applet_datadir)/icons
dist_custom_icon_DATA = \
	icons/comics-icon.svg \
	icons/default.svg \
	icons/error.svg \
	$(NULL)
