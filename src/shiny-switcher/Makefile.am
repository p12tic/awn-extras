INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)						\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                  

SHINYSWITCHER_SOURCES =                              \
	applet.c									\
	shinyswitcherapplet.c  \
	shinyswitcherapplet.h


SHINYSWITCHER_LDADD =                        \
        $(DEPS_LIBS)			        
        

shinyswitcherlibdir = $(libdir)/awn/applets/shinyswitcher
shinyswitcherlib_LTLIBRARIES = shinyswitcher.la
shinyswitcher_la_SOURCES = $(SHINYSWITCHER_SOURCES)
shinyswitcher_la_LIBADD = $(SHINYSWITCHER_LDADD)
shinyswitcher_la_LDFLAGS = -module -avoid-version
shinyswitcher_la_CFLAGS =

schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_FILE = shinyswitcher.schemas
schemas_in_files = $(schemas_FILE).in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif

icondir = $(pkgdatadir)

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	shinyswitcher.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA): $(desktop_DATA).in
	sed -e "s|\@LIBDIR\@|$(libdir)|g;s|\@ICONDIR\@|$(icondir)|g" $< > $@


EXTRA_DIST = \
	$(icon_DATA) \
        $(desktop_DATA).in

CLEANFILES = $(desktop_DATA)
