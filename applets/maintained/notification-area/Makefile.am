APPLET_NAME = notification-area
APPLET_ICONS = notification-area.svg
APPLET_CFLAGS = $(DEFS) -I$(top_builddir) -DAPPLET_NAME='\"$(APPLET_NAME)\"'
#$(LIBX11_CFLAGS)

VALA_FILES = \
	notification-area.vala	\
	na-prefs.vala		\
	eggtraymanager.c	\
        egg-tray-child.c        \
	eggmarshalers.c		\
	egg-tray.vapi		\
	build.vapi		\
	$(NULL)

VALAFLAGS = --pkg x11 --pkg desktop-agnostic

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
