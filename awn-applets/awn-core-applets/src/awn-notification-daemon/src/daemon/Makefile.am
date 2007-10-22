INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"    \
	-I$(top_srcdir) \
	$(NOTIFICATION_DAEMON_CFLAGS) \
	-DENGINES_DIR=\"$(libdir)/notification-daemon-1.0/engines\"
	

AWNNOTIFICATIONDAEMON_SOURCES = \
	daemon.c \
	daemon.h \
	engines.c \
	engines.h \
	stack.c \
	stack.h

AWNNOTIFICATIONDAEMON_LDADD =                        \
        $(DEPS_LIBS)    \
        $(NOTIFICATION_DAEMON_LIBS)

awnnotificationdaemonlibdir = $(libdir)/awn/applets/awnnotificationdaemon
awnnotificationdaemonlib_LTLIBRARIES = awnnotificationdaemon.la
awnnotificationdaemon_la_SOURCES = $(AWNNOTIFICATIONDAEMON_SOURCES)
awnnotificationdaemon_la_LIBADD = $(AWNNOTIFICATIONDAEMON_LDADD)
awnnotificationdaemon_la_LDFLAGS = -module -avoid-version
awnnotificationdaemon_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	awnnotificationdaemon.desktop
@INTLTOOL_DESKTOP_RULE@


$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	awnnotificationdaemon.desktop.in.in  \
	notificationdaemon.xml

CLEANFILES = $(desktop_DATA) stack.schemas

BUILT_SOURCES = notificationdaemon-dbus-glue.h

notificationdaemon-dbus-glue.h: notificationdaemon.xml
	dbus-binding-tool --mode=glib-server --prefix=notification_daemon \
		$(srcdir)/notificationdaemon.xml > notificationdaemon-dbus-glue.h

DISTCLEANFILES = \
	notificationdaemon-dbus-glue.h
