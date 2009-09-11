APPLET_NAME = awnnotificationdaemon
APPLET_CFLAGS =								\
	$(NOTIFICATION_DAEMON_CFLAGS)					\
	-DENGINES_DIR=\"$(libdir)/notification-daemon-1.0/engines\"

include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = awnnotificationdaemon.la

awnnotificationdaemon_la_SOURCES =	\
	daemon.c			\
	daemon.h			\
	engines.c			\
	engines.h			\
	sound.c				\
	sound.h				\
	stack.c				\
	stack.h				\
	$(NULL)
awnnotificationdaemon_la_LIBADD =	\
	$(AWN_LIBS)			\
	$(NOTIFICATION_DAEMON_LIBS)	\
	$(NULL)
awnnotificationdaemon_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

BUILT_SOURCES = notificationdaemon-dbus-glue.h

notificationdaemon-dbus-glue.h: notificationdaemon.xml
	dbus-binding-tool --mode=glib-server --prefix=notification_daemon $< > $@

# config

if GCONF_SCHEMAS_INSTALL
schemasdir       = $(GCONF_SCHEMA_FILE_DIR)
schemas_in_files = awn-notification-daemon.schemas.in
schemas_DATA     = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

install-data-local:
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
else
install-data-local:
endif

CLEANFILES += $(schemas_DATA)

DISTCLEANFILES = \
	notificationdaemon-dbus-glue.h \
	$(NULL)

EXTRA_DIST += \
	AUTHORS NEWS INSTALL COPYING README \
	ChangeLog \
	notificationdaemon.xml \
	$(schemas_in_files) \
	$(NULL)
