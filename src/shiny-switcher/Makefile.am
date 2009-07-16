APPLET_NAME = shinyswitcher
APPLET_CFLAGS = $(SHINY_SWITCHER_CFLAGS) -std=c99

include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = shinyswitcher.la

shinyswitcher_la_SOURCES =	\
	applet.c		\
	shinyswitcherapplet.c	\
	shinyswitcherapplet.h	\
	$(NULL)
shinyswitcher_la_LIBADD =	\
	$(AWN_LIBS)		\
	$(SHINY_SWITCHER_LIBS)	\
	$(NULL)
shinyswitcher_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

prefsdir = $(applet_datadir)
dist_prefs_DATA =		\
	shiny-prefs.glade	\
	shiny-prefs.py		\
	$(NULL)
