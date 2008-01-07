INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)						\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                  

CAIRO_MAIN_MENU_SOURCES =                              \
	applet.c									\
	backend-gnome.c								\
	backend-gnome.h								\
	menu.c										\
	menu.h										\
	menu_list_item.h							\
	render.c									\
	render.h									\
	config_entries.c									\
	config_entries.h

CAIRO_MAIN_MENU_LDADD =                        \
        $(DEPS_LIBS)			        
        

cairo_main_menulibdir = $(libdir)/awn/applets/cairo_main_menu
cairo_main_menulib_LTLIBRARIES = cairo_main_menu.la
cairo_main_menu_la_SOURCES = $(CAIRO_MAIN_MENU_SOURCES)
cairo_main_menu_la_LIBADD = $(CAIRO_MAIN_MENU_LDADD)
cairo_main_menu_la_LDFLAGS = -module -avoid-version
cairo_main_menu_la_CFLAGS =

icondir = $(pkgdatadir)

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	cairo_main_menu.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA): $(desktop_DATA).in
	sed -e "s|\@LIBDIR\@|$(libdir)|g;s|\@ICONDIR\@|$(icondir)|g" $< > $@


EXTRA_DIST = \
	$(icon_DATA) \
        $(desktop_DATA).in

CLEANFILES = $(desktop_DATA)
