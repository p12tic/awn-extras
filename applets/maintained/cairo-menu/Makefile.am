APPLET_NAME = cairo-menu
GNOME_MENU_BUILDER = gnome-menu-builder

APPLET_CFLAGS = $(NULL)
if CAIRO_MENU_GNOME3
APPLET_CFLAGS += \
     $(CAIRO_MENU_GNOME3_FLAGS) \
     $(NULL)
else
APPLET_CFLAGS += \
     $(CAIRO_MENU_GNOME_FLAGS) \
     $(NULL)
endif
APPLET_CFLAGS +=				\
	-std=c99 \
	-D_GNU_SOURCE \
	$(NULL)

include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

gnome_menu_builderdir = $(appletdir)

applet_LTLIBRARIES = cairo-menu.la
cairo_menu_la_SOURCES =	\
	applet.c				\
	cairo-menu-applet.c        \
	cairo-menu-applet.h        \
	cairo-main-icon.c       \
	cairo-main-icon.h       \
	cairo-aux-icon.c       \
	cairo-aux-icon.h       \
	misc.h                  \
	misc.c                  \
	$(NULL)
cairo_menu_la_LIBADD =	\
	$(AWN_LIBS)				\
        $(NULL)
if CAIRO_MENU_GNOME3
cairo_menu_la_LIBADD += \
    $(CAIRO_MENU_GNOME3_LIBS)\
    $(NULL)
else
cairo_menu_la_LIBADD += \
    $(CAIRO_MENU_GNOME3_LIBS) \
    $(NULL)
endif
cairo_menu_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

gnome_menu_builder_LTLIBRARIES = gnome-menu-builder.la
gnome_menu_builder_la_SOURCES =	\
	gnome-menu-builder.h      \
	cairo-menu.c            \
	cairo-menu.h            \
	cairo-menu-item.c       \
	cairo-menu-item.h       \
	misc.h                  \
	misc.c                  \
	$(NULL)
if CAIRO_MENU_GNOME3
gnome_menu_builder_la_SOURCES += \
    gnome-menu-builder-gnome3.c \
    $(NULL)
else
gnome_menu_builder_la_SOURCES += \
    gnome-menu-builder.c \
    $(NULL)
endif
gnome_menu_builder_la_LIBADD =	\
    $(AWN_LIBS)				\
    $(NULL)
if CAIRO_MENU_GNOME3
gnome_menu_builder_la_LIBADD +=	\
    $(CAIRO_MENU_GNOME3_LIBS) \
    $(NULL)
else
gnome_menu_builder_la_LIBADD +=	\
    $(CAIRO_MENU_GNOME_LIBS) \
    $(NULL)
endif
gnome_menu_builder_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

