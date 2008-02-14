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
	dbus-binding-tool --mode=glib-server --prefix=notification_daemon \
		$(srcdir)/notificationdaemon.xml > notificationdaemon-dbus-glue.h

DISTCLEANFILES = \
	notificationdaemon-dbus-glue.h
