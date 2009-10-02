APPLET_NAME = notification-area
APPLET_ICONS = notification-area.svg
APPLET_CFLAGS = $(LIBX11_CFLAGS) -I$(top_builddir)

VALA_FILES = \
	notification-area.vala	\
	na-prefs.vala		\
	egg-tray.vapi		\
	$(NULL)

AM_VALAFLAGS = \
	--pkg desktop-agnostic-gtk \
	--pkg x11 \
	$(NULL)

APPLET_LIBS = \
	$(AWN_LIBS)		\
	$(LIBX11_LIBS)		\
	$(NULL)

include $(top_srcdir)/Makefile.vala-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = notification-area.la
notification_area_la_SOURCES = \
	$(VALA_C_FILES) \
	eggtraymanager.c \
	egg-tray-child.c \
	eggmarshalers.c \
	$(NULL)
notification_area_la_LIBADD = \
	$(AWN_LIBS) \
	$(LIBX11_LIBS) \
	$(NULL)
notification_area_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

prefsdir = $(applet_datadir)
dist_prefs_DATA =	\
	na-prefs.ui	\
	$(NULL)

EXTRA_DIST += $(wildcard *.h)

# vim: set ts=8 sts=8 sw=8 :
