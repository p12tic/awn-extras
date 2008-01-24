APPLET_NAME = trasher
APPLET_CFLAGS = $(GNOME_CFLAGS) $(GNOME_VFS_CFLAGS)
include $(top_srcdir)/Makefile.c-applet
applet_LTLIBRARIES = trasher.la
trasher_la_SOURCES =	\
	applet.c	\
	$(NULL)
trasher_la_LIBADD =		\
	$(AWN_LIBS)		\
	$(GNOME_LIBS)		\
	$(GNOME_VFS_LIBS)	\
	$(NULL)
trasher_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
