APPLET_NAME = cairo-menu
GNOME_MENU_BUILDER = gnome-menu-builder

APPLET_CFLAGS =				\
	$(CAIRO_MENU_GNOME_CFLAGS) \
	-D_GNU_SOURCE

include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

gnome_menu_builderdir = $(appletdir)

applet_LTLIBRARIES = cairo-menu.la
cairo_menu_la_SOURCES =	\
	applet.c				\
	cairo-menu-applet.c        \
	cairo-menu-applet.h        \
	cairo-menu.c            \
	cairo-menu.h            \
	cairo-menu-item.c       \
	cairo-menu-item.h       \
	cairo-main-icon.c       \
	cairo-main-icon.h       \
	misc.h                  \
	misc.c                  \
	$(NULL)
cairo_menu_la_LIBADD =	\
	$(AWN_LIBS)				\
	$(CAIRO_MENU_GNOME_LIBS)		\
        $(NULL)
cairo_menu_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

gnome_menu_builder_LTLIBRARIES = gnome-menu-builder.la
gnome_menu_builder_la_SOURCES =	\
	gnome-menu-builder.h      \
	gnome-menu-builder.c      \
	cairo-menu.c            \
	cairo-menu.h            \
	cairo-menu-item.c       \
	cairo-menu-item.h       \	
	misc.h                  \
	misc.c                  \
	$(NULL)
gnome_menu_builder_la_LIBADD =	\
	$(AWN_LIBS)				\
	$(CAIRO_MENU_GNOME_LIBS)		\
        $(NULL)
gnome_menu_builder_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

