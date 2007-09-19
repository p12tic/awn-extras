INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"    

CPUMETER_SOURCES =                              \
	applet.c									\
	dashboard.c		\
	dashboard.h		\
	awntop.c    \
	awntop.h    \
	cpumeterapplet.c						\
	cpumeterapplet.h          \
	cpumetergconf.c           \
	cpumetergconf.h           \
	config.h

CPUMETER_LDADD =                        \
        $(DEPS_LIBS)

cpumeterlibdir = $(libdir)/awn/applets/cpumeter
cpumeterlib_LTLIBRARIES = cpumeter.la
cpumeter_la_SOURCES = $(CPUMETER_SOURCES)
cpumeter_la_LIBADD = $(CPUMETER_LDADD)
cpumeter_la_LDFLAGS = -module -avoid-version
cpumeter_la_CFLAGS =

schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_FILE = cpumeter.schemas
schemas_in_files = $(schemas_FILE).in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	cpumeter.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	cpumeter.desktop.in.in  \
	cpumeter.schema.in.in

CLEANFILES = $(desktop_DATA) stack.schemas
