INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                 

CLOCK_SOURCES =                              \
	applet.c				\
	clock-applet.h				\
	clock-applet.c				\
	utils.c					\
	utils.h

CLOCK_LDADD =                        \
        $(DEPS_LIBS)
        

clocklibdir = $(libdir)/awn/applets/clock
clocklib_LTLIBRARIES = clock.la
clock_la_SOURCES = $(CLOCK_SOURCES)
clock_la_LIBADD = $(CLOCK_LDADD)
clock_la_LDFLAGS = -module -avoid-version 
clock_la_CFLAGS =


schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_in_files = awn-clock.schemas.in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif


desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	clock.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	clock.desktop.in.in 			\
	awn.clock.schemas.in
