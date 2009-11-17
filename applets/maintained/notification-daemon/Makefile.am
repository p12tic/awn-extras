APPLET_NAME = notification-daemon
APPLET_CFLAGS =								\
	$(NOTIFICATION_DAEMON_CFLAGS)					\
	-DENGINES_DIR=\"$(libdir)/notification-daemon-1.0/engines\"

include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = notification-daemon.la

notification_daemon_la_SOURCES =	\
	daemon.c			\
	daemon.h			\
	engines.c			\
	engines.h			\
	sound.c				\
	sound.h				\
	stack.c				\
	stack.h				\
	$(NULL)
notification_daemon_la_LIBADD =	\
	$(AWN_LIBS)			\
	$(NOTIFICATION_DAEMON_LIBS)	\
	$(NULL)
notification_daemon_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

BUILT_SOURCES = notificationdaemon-dbus-glue.h

notificationdaemon-dbus-glue.h: notificationdaemon.xml
	dbus-binding-tool --mode=glib-server --prefix=notification_daemon $< > $@

# config

#install-data-local:

CLEANFILES += $(schemas_DATA)

DISTCLEANFILES = \
	notificationdaemon-dbus-glue.h \
	$(NULL)

EXTRA_DIST += \
	AUTHORS NEWS INSTALL COPYING README \
	ChangeLog \
	notificationdaemon.xml \
	$(NULL)
