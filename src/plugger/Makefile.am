APPLET_NAME = plugger
APPLET_CFLAGS = $(PLUGGER_CFLAGS) -DPREFIX=\"$(prefix)\"
include $(top_srcdir)/Makefile.c-applet
applet_LTLIBRARIES = plugger.la
plugger_la_SOURCES =	\
	applet.c	\
	$(NULL)
plugger_la_LIBADD =	\
	$(AWN_LIBS)	\
	$(PLUGGER_LIBS)	\
	$(NULL)
plugger_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
