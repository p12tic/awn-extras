APPLET_NAME = awnterm
APPLET_CFLAGS = $(VTE_CFLAGS)
include $(top_srcdir)/Makefile.c-applet
applet_LTLIBRARIES = awnterm.la
awnterm_la_SOURCES =	\
	applet.c	\
	awnterm.c	\
	awnterm.h	\
	settings.c	\
	settings.h	\
	$(NULL)
awnterm_la_LIBADD =	\
	$(AWN_LIBS)	\
	$(VTE_LIBS)	\
	$(NULL)
awnterm_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_FILE = awn-terminal.schemas
schemas_in_files = $(schemas_FILE).in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif
