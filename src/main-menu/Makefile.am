APPLET_NAME = main-menu
APPLET_CFLAGS = $(GNOME_MENU_CFLAGS) $(GNOME_DESKTOP_CFLAGS)
include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = main-menu.la
main_menu_la_SOURCES = applet.c
main_menu_la_LIBADD =		\
	$(AWN_LIBS)		\
	$(GNOME_MENU_LIBS)	\
	$(GNOME_DESKTOP_LIBS)	\
	$(NULL)
main_menu_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
