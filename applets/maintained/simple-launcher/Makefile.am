APPLET_NAME = simple-launcher
#APPLET_ICONS = system-run.svg
APPLET_CFLAGS = \
	-std=c99 \
	-I$(top_builddir) \
	$(NULL)

VALA_FILES = \
	simple-launcher.vala	\
	$(NULL)

AM_VALAFLAGS = \
	--pkg desktop-agnostic-fdo \
	--pkg desktop-agnostic-ui \
	$(NULL)

APPLET_LIBS = \
	$(AWN_LIBS)		\
	$(NULL)

include $(top_srcdir)/Makefile.vala-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = simple-launcher.la
simple_launcher_la_SOURCES = \
	$(VALA_C_FILES) \
	$(NULL)
simple_launcher_la_LIBADD = \
	$(AWN_LIBS) \
	$(NULL)
simple_launcher_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

#prefsdir = $(applet_datadir)
#dist_prefs_DATA =	\
#	na-prefs.ui	\
#	$(NULL)

#EXTRA_DIST += $(wildcard *.h)

# vim: set ts=8 sts=8 sw=8 :
