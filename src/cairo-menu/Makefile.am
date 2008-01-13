APPLET_NAME = cairo_main_menu
APPLET_CFLAGS =				\
	$(CAIRO_MENU_GNOME_CFLAGS)

include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = cairo_main_menu.la
cairo_main_menu_la_SOURCES =	\
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
cairo_main_menu_la_LIBADD =	\
	$(AWN_LIBS)				\
	$(CAIRO_MENU_GNOME_LIBS)		\
        $(NULL)
cairo_main_menu_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
