APPLET_NAME = main-menu
APPLET_CFLAGS = $(GNOME_MENU_CFLAGS)
include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = main-menu.la
main_menu_la_SOURCES = applet.c
main_menu_la_LIBADD =		\
	$(AWN_LIBS)		\
	$(GNOME_MENU_LIBS)	\
	$(top_builddir)/src/libawn-extras/libawn-extras.la	\
	$(NULL)
main_menu_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
