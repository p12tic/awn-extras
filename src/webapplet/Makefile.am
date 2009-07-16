APPLET_NAME = webapplet
APPLET_CFLAGS = $(WEBAPPLET_CFLAGS)

include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = webapplet.la

webapplet_la_SOURCES =	\
	applet.c	\
	applet.h	\
	engine_html.c	\
	engine_html.h	\
	configuration.c	\
	configuration.h	\
	$(NULL)

if WITH_MOZILLA
webapplet_la_SOURCES +=	\
	engine_mozilla.c	\
	engine_mozilla.h	\
	$(NULL)
endif

if WITH_WEBKIT
webapplet_la_SOURCES +=	\
	engine_webkit.c	\
	engine_webkit.h	\
	$(NULL)
endif

webapplet_la_LIBADD =		\
	$(WEBAPPLET_LIBS)	\
	$(AWN_LIBS)		\
	$(NULL)
webapplet_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

inifile_DATA = webapplet-websites.ini
inifiledir = $(applet_datadir)

web_iconsdir = $(applet_datadir)/icons
dist_web_icons_DATA =		\
	icons/brightkite-22.png	\
	icons/brightkite.svg	\
	icons/digg-22.png	\
	icons/digg.svg		\
	icons/facebook-22.png	\
	icons/facebook.svg	\
	icons/friendfeed-22.png	\
	icons/friendfeed.svg	\
	icons/meebo-48.png	\
	icons/pandora-48.png	\
	icons/pingfm-22.png	\
	icons/pingfm.svg	\
	icons/rtm.png		\
	icons/twitter-22.png	\
	icons/twitter.svg	\
	$(NULL)
