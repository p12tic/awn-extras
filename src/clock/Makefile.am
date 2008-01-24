APPLET_NAME = clock
APPLET_CFLAGS = $(RSVG_CFLAGS)
include $(top_srcdir)/Makefile.c-applet
applet_LTLIBRARIES = clock.la
clock_la_SOURCES =	\
	applet.c	\
	clock-applet.h	\
	clock-applet.c	\
	utils.c		\
	utils.h		\
	$(NULL)
clock_la_LIBADD =	\
	$(AWN_LIBS)	\
	$(RSVG_LIBS)	\
	$(NULL)
clock_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

schemasdir = @GCONF_SCHEMA_FILE_DIR@
schemas_in_files = awn-clock.schemas.in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif

EXTRA_DIST += $(schemas_in_files)
