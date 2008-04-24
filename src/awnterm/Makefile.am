APPLET_NAME = awnterm
APPLET_CFLAGS = $(VTE_CFLAGS)
include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas
applet_LTLIBRARIES = awnterm.la
awnterm_la_SOURCES =	\
	applet.c	\
	awnterm.c	\
	awnterm.h	\
	settings.c	\
	settings.h	\
	$(NULL)
awnterm_la_LIBADD =	\
	$(AWN_LIBS)	\
	$(VTE_LIBS)	\
	$(top_builddir)/src/libawn-extras/libawn-extras.la	\
	$(NULL)
awnterm_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
