INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"    

AWNSYSTEMMONITOR_SOURCES =                              \
	applet.c									\
	dashboard.c		\
	dashboard.h		\
	awntop.c    \
	awntop.h    \
	awntop_cairo_component.c    \
	awntop_cairo_component.h    \
	awnsystemmonitor.c						\
	awnsystemmonitor.h          \
	cpumetergconf.c           \
	cpumetergconf.h           \
	uptime_component.c      \
	uptime_component.h      \
	dashboard_util.c    \
	dashboard_util.h    \
	cpu_component.c    \
    cpu_component.h    \
    date_time_component.c   \
    date_time_component.h   \
    loadavg_component.c \
    loadavg_component.h \
	config.h

AWNSYSTEMMONITOR_LDADD =                        \
        $(DEPS_LIBS)

awnsystemmonitorlibdir = $(libdir)/awn/applets/awnsystemmonitor
awnsystemmonitorlib_LTLIBRARIES = awnsystemmonitor.la
awnsystemmonitor_la_SOURCES = $(AWNSYSTEMMONITOR_SOURCES)
awnsystemmonitor_la_LIBADD = $(AWNSYSTEMMONITOR_LDADD)
awnsystemmonitor_la_LDFLAGS = -module -avoid-version
awnsystemmonitor_la_CFLAGS =

schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_FILE = awnsystemmonitor.schemas
schemas_in_files = $(schemas_FILE).in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	awn-system-monitor.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	awn-system-monitor.desktop.in.in  \
	$(schemas_in_files)

CLEANFILES = $(desktop_DATA) 
