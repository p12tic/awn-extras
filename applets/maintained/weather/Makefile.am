SUBDIRS = locale
APPLET_NAME = weather
APPLET_MAIN_FILE = weather.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA = 		\
	messages.pot		\
	forecast.py          \
	weather.ui	\
	$(NULL)

moonbeam_themedir = $(applet_datadir)/themes/moonbeam
dist_moonbeam_theme_DATA = $(wildcard themes/moonbeam/*.png)
