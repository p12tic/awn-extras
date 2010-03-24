APPLET_NAME = awnsystemmonitor
APPLET_CFLAGS = \
	$(AWN_SYSTEM_MONITOR_CFLAGS) \
	-std=c99 \
	-D_GNU_SOURCE \
	$(NULL)
include $(top_srcdir)/Makefile.c-applet
applet_LTLIBRARIES = awnsystemmonitor.la
awnsystemmonitor_la_SOURCES =		\
	applet.c			\
	awnsystemmonitor.c		\
	awnsystemmonitor.h		\
	awntop.c			\
	awntop.h			\
	awntop_cairo_component.c	\
	awntop_cairo_component.h	\
	cairo-utils.c \
	cairo-utils.h \
	cpumetergconf.c			\
	cpumetergconf.h			\
	cpu_component.c			\
	cpu_component.h			\
	dashboard.c			\
	dashboard.h			\
	dashboard_util.c		\
	dashboard_util.h		\
	date_time_component.c		\
	date_time_component.h		\
	gconf-config.h \
	loadavg_component.c		\
	loadavg_component.h		\
	sysmem_component.c		\
	sysmem_component.h		\
	uptime_component.c		\
	uptime_component.h		
	$(NULL)
awnsystemmonitor_la_LIBADD =					\
	$(AWN_LIBS)						\
	$(AWN_SYSTEM_MONITOR_LIBS)				\
	$(NULL)
awnsystemmonitor_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

schemasdir = @GCONF_SCHEMA_FILE_DIR@
schemas_FILE = awnsystemmonitor.schemas
schemas_in_files = $(schemas_FILE).in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif

EXTRA_DIST += $(schemas_in_files)
DISTCLEANFILES = $(schemas_FILE)

