SUBDIRS = icons
APPLET_NAME = wobblyzini

include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = wobblyzini.la
wobblyzini_la_SOURCES =	\
	applet.c			\
	wobblyziniapplet.c	\
	wobblyziniapplet.h	\
	$(NULL)
wobblyzini_la_LIBADD =	\
	$(AWN_LIBS)			\
	$(NULL)
wobblyzini_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
