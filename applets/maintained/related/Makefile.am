APPLET_NAME = related
APPLET_ICONS = zeitgeist-logo.svg
APPLET_CFLAGS = \
	-std=c99 \
	-I$(top_builddir) \
	-DWNCK_I_KNOW_THIS_IS_UNSTABLE \
	$(LIBWNCK_CFLAGS) \
	$(GTOP_CFLAGS) \
	$(ZEITGEIST_CFLAGS) \
	$(NULL)

VALA_FILES = \
	related-applet.vala	\
	$(NULL)

AM_VALAFLAGS = \
	--pkg zeitgeist-1.0 \
	--pkg libwnck-1.0 \
	--pkg dbus-glib-1 \
	--pkg gio-unix-2.0 \
	$(srcdir)/desktop-lookup.vapi \
	$(NULL)

APPLET_LIBS = \
	$(AWN_LIBS)		\
	$(LIBWNCK_LIBS)		\
	$(GTOP_LIBS)		\
	$(ZEITGEIST_LIBS)	\
	$(NULL)

include $(top_srcdir)/Makefile.vala-applet
#include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = related.la
related_la_SOURCES = \
	$(VALA_C_FILES) \
	awn-desktop-lookup.c \
	awn-desktop-lookup-cached.c \
	xutils.c \
	util.c \
	$(NULL)
related_la_LIBADD = \
	$(AWN_LIBS) \
	$(LIBWNCK_LIBS) \
	$(GTOP_LIBS) \
	$(ZEITGEIST_LIBS) \
	$(NULL)
related_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

#prefsdir = $(applet_datadir)
#dist_prefs_DATA =	\
#	na-prefs.ui	\
#	$(NULL)

EXTRA_DIST += $(wildcard *.h)

# vim: set ts=8 sts=8 sw=8 :
