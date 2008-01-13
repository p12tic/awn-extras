INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(AWN_CFLAGS)						\
	$(GNOME_MENU_CFLAGS)				\
	$(GNOME_DESKTOP_CFLAGS)				\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"

MENU_SOURCES = \
	applet.c

MENU_LDADD =                        \
        $(AWN_LIBS)					\
		$(GNOME_MENU_LIBS)			\
		$(GNOME_DESKTOP_LIBS)

mainmenulibdir = $(libdir)/awn/applets/mainmenu
mainmenulib_LTLIBRARIES = mainmenu.la
mainmenu_la_SOURCES = $(MENU_SOURCES)
mainmenu_la_LIBADD = $(MENU_LDADD)
mainmenu_la_LDFLAGS = -module -avoid-version
mainmenu_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	main-menu.desktop

@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	main-menu.desktop.in.in
