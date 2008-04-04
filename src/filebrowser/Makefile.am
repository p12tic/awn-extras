APPLET_NAME = filebrowser
APPLET_CFLAGS =	$(FILEBROWSER_CFLAGS)
APPLET_ICONS = filebrowser.svg
include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = filebrowser.la
filebrowser_la_SOURCES =	\
	filebrowser-applet.c	\
	filebrowser-applet.h	\
	filebrowser-defines.h	\
	filebrowser-dialog.c	\
	filebrowser-dialog.h	\
	filebrowser-folder.c	\
	filebrowser-folder.h	\
	filebrowser-gconf.c	\
	filebrowser-gconf.h	\
	filebrowser-icon.c	\
	filebrowser-icon.h	\
	filebrowser-utils.c	\
	filebrowser-utils.h	\
	$(NULL)
filebrowser_la_LIBADD =		\
	$(AWN_LIBS)		\
	$(FILEBROWSER_LIBS)	\
	$(NULL)
filebrowser_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

EXTRA_DIST += filebrowser.svg
