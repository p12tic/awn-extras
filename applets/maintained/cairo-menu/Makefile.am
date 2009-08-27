APPLET_NAME = cairo-menu
APPLET_CFLAGS =				\
	$(CAIRO_MENU_GNOME_CFLAGS) \
	-D_GNU_SOURCE

include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = cairo-menu.la
cairo_menu_la_SOURCES =	\
	applet.c				\
	backend-gnome.c				\
	backend-gnome.h				\
	menu.c					\
	menu.h					\
	menu_list_item.h			\
	render.c				\
	render.h				\
	config_entries.c			\
	config_entries.h			\
	$(NULL)
cairo_menu_la_LIBADD =	\
	$(AWN_LIBS)				\
	$(CAIRO_MENU_GNOME_LIBS)		\
        $(NULL)
cairo_menu_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
