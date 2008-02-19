APPLET_NAME = switcher
APPLET_CFLAGS = $(LIBWNCK_CFLAGS)
include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas
applet_LTLIBRARIES = switcher.la
switcher_la_SOURCES =	\
	applet.c	\
	$(NULL)
switcher_la_LIBADD =	\
	$(AWN_LIBS)	\
	$(LIBWNCK_LIBS)	\
	$(NULL)
switcher_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

EXTRA_DIST=switcher.schema-ini
