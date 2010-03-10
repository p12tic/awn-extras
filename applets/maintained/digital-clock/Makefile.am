APPLET_NAME = digital-clock
APPLET_ICONS = awn-applet-digital-clock.svg
VALA_FILES = \
	digital-clock.vala \
	dg-prefs.vala \
	$(NULL)
AM_VALAFLAGS = \
	--pkg libintl \
	$(NULL)

include $(top_srcdir)/Makefile.vala-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = digital-clock.la
digital_clock_la_SOURCES = \
	$(VALA_C_FILES) \
	$(NULL)
digital_clock_la_LIBADD = \
	$(AWN_LIBS) \
	$(NULL)
digital_clock_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

prefsdir = $(applet_datadir)
dist_prefs_DATA =       \
	dg-prefs.ui     \
	$(NULL)

# vim: set ts=8 sts=8 sw=8 :
