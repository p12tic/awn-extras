APPLET_NAME = trash
APPLET_CFLAGS = 					\
	$(GNOMEUI_CFLAGS)				\
	$(LIBGLADE_CFLAGS)				\
	-DGLADEDIR=\"$(libdir)/awn/applets/trash\"	\
	$(NULL)
include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas
applet_LTLIBRARIES = trash.la
trash_la_SOURCES =	\
	applet.c	\
	trashapplet.c	\
	trashapplet.h	\
	trash-monitor.c	\
	trash-monitor.h	\
	xstuff.c	\
	xstuff.h	\
	$(NULL)
trash_la_LIBADD =		\
	$(AWN_LIBS)		\
	$(GNOMEUI_LIBS)		\
	$(LIBGLADE_LIBS)	\
	$(NULL)
trash_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
gladedir = $(libdir)/awn/applets/trash
glade_DATA = trashapplet.glade
EXTRA_DIST += 			\
	trashapplet.glade	\
	$(NULL)

EXTRA_DIST=trash.schema-ini trashapplet.glade
