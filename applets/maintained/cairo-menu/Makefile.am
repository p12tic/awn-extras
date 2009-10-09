APPLET_NAME = cairo-menu
APPLET_CFLAGS =				\
	$(CAIRO_MENU_GNOME_CFLAGS) \
	-D_GNU_SOURCE

include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = cairo-menu.la
cairo_menu_la_SOURCES =	\
	applet.c				\
	cairo-menu-applet.c        \
	cairo-menu-applet.h        \
	cairo-menu.c            \
	cairo-menu.h            \
	cairo-menu-item.c       \
	cairo-menu-item.h       \
	gnome-menu-builder.h      \
	gnome-menu-builder.c      \
	$(NULL)
cairo_menu_la_LIBADD =	\
	$(AWN_LIBS)				\
	$(CAIRO_MENU_GNOME_LIBS)		\
        $(NULL)
cairo_menu_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
