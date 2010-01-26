APPLET_NAME = trasher
APPLET_CFLAGS = $(TRASHER_CFLAGS) -DPREFIX=\"$(prefix)\"
include $(top_srcdir)/Makefile.c-applet
applet_LTLIBRARIES = trasher.la
trasher_la_SOURCES =	\
	applet.c	\
	$(NULL)
trasher_la_LIBADD =	\
	$(AWN_LIBS)	\
	$(TRASHER_LIBS)	\
	$(NULL)
trasher_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
