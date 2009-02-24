APPLET_NAME = notification-area
APPLET_ICONS = notification-area.svg
APPLET_CFLAGS = $(LIBX11_CFLAGS)

include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = notification-area.la
notification_area_la_SOURCES =	\
	applet.c		\
	eggtraymanager.c	\
	eggtraymanager.h	\
        egg-tray-child.c        \
        egg-tray-child.h        \
	eggmarshalers.c		\
	eggmarshalers.h		\
	$(NULL)
notification_area_la_LIBADD =	\
	$(AWN_LIBS)		\
	$(LIBX11_LIBS)		\
	$(NULL)
notification_area_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
