APPLET_NAME = cairo-clock
APPLET_MAIN_FILE = cairo-clock.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA =  \
    cairo-clock-logo.svg \
    cairo-clock.ui \
    analogclock.py \
    locations.py \
    sun.py \
    weather.py \
    $(NULL)

gnome_themedir = $(applet_datadir)/themes/gnome
dist_gnome_theme_DATA = $(wildcard $(srcdir)/themes/gnome/*.svg)

onox_themedir = $(applet_datadir)/themes/onox
dist_onox_theme_DATA = $(wildcard $(srcdir)/themes/onox/*.svg)

tango_themedir = $(applet_datadir)/themes/tango
dist_tango_theme_DATA = $(wildcard $(srcdir)/themes/tango/*.svg)
