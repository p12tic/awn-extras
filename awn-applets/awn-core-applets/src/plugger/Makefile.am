INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)				\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                  

PLUGGER_SOURCES =                              \
	applet.c

PLUGGER_LDADD =                        \
        $(DEPS_LIBS)			        
        

pluggerlibdir = $(libdir)/awn/applets/plugger
pluggerlib_LTLIBRARIES = plugger.la
plugger_la_SOURCES = $(PLUGGER_SOURCES)
plugger_la_LIBADD = $(PLUGGER_LDADD)
plugger_la_LDFLAGS = -module -avoid-version
plugger_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	plugger.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_in_files = plugger.schemas.in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif

EXTRA_DIST = \
	plugger.desktop.in.in			\
	plugger.schemas.in
