INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"    

AWNTERM_SOURCES =                                            \
	applet.c awnterm.c awnterm.h settings.c settings.h

AWNTERM_LDADD =                        \
        $(DEPS_LIBS)
        

awntermlibdir = $(libdir)/awn/applets/awnterm
awntermlib_LTLIBRARIES = awnterm.la
awnterm_la_SOURCES = $(AWNTERM_SOURCES)
awnterm_la_LIBADD = $(AWNTERM_LDADD)
awnterm_la_LDFLAGS = -module -avoid-version
awnterm_la_CFLAGS =

schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_FILE = awn-terminal.schemas
schemas_in_files = $(schemas_FILE).in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	awnterm.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	awnterm.desktop.in.in
