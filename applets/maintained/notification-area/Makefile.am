APPLET_NAME = notification-area
APPLET_ICONS = notification-area.svg
APPLET_CFLAGS = $(LIBX11_CFLAGS) -I$(top_builddir)

VALA_FILES = \
	notification-area.vala	\
	na-prefs.vala		\
	eggtraymanager.c	\
        egg-tray-child.c        \
	eggmarshalers.c		\
	egg-tray.vapi		\
	$(NULL)

AM_VALAFLAGS = \
	--pkg x11 \
	$(NULL)

APPLET_LIBS = \
	$(AWN_LIBS)		\
	$(LIBX11_LIBS)		\
	$(NULL)

include $(top_srcdir)/Makefile.vala-applet
include $(top_srcdir)/Makefile.schemas

prefsdir = $(applet_datadir)
dist_prefs_DATA =	\
	na-prefs.xml	\
	$(NULL)
# vim: set ts=8 sts=8 sw=8 :
