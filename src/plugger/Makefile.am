APPLET_NAME = plugger
APPLET_CFLAGS = $(GNOME_CFLAGS) $(GNOME_VFS_CFLAGS) -DPREFIX=\"$(prefix)\"
include $(top_srcdir)/Makefile.c-applet
applet_LTLIBRARIES = plugger.la
plugger_la_SOURCES =	\
	applet.c	\
	$(NULL)
plugger_la_LIBADD =		\
	$(AWN_LIBS)		\
	$(GNOME_LIBS)		\
	$(GNOME_VFS_LIBS)	\
	$(NULL)
plugger_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
