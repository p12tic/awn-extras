SUBDIRS = images locale
APPLET_NAME = weather
APPLET_MAIN_FILE = weather.py
include $(top_srcdir)/Makefile.python-applet
dist_applet_DATA = 		\
	messages.pot		\
	forecast.py          \
	weathericons.py		\
	weather-prefs.glade	\
	$(NULL)

moonbeam_themedir = $(applet_datadir)/themes/moonbeam
dist_moonbeam_theme_DATA = $(wildcard themes/moonbeam/*.png)