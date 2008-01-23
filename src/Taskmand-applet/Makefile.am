APPLET_NAME = Taskmand-applet

include $(top_srcdir)/Makefile.c-applet

APPLET_CFLAGS =								\
	$(TASKMAND_APPLET_CFLAGS)

applet_LTLIBRARIES = Taskmand-applet.la
Taskmand_applet_la_SOURCES = \
	applet.c		\
	$(NULL)
Taskmand_applet_la_LIBADD =										\
	$(AWN_LIBS)											\
	$(NULL)
Taskmand_applet_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

BUILT_SOURCES = server-bindings.h client-bindings.h
# We don't want to install this header
noinst_HEADERS = $(BUILT_SOURCES)

# Correctly clean the generated headers, but keep the xml description

EXTRA_DIST = taskmand-infos.xml

#Rule to generate the binding headers
server-bindings.h:  taskmand-infos.xml
	dbus-binding-tool --prefix=taskmand --mode=glib-server $<> $@

client-bindings.h:  taskmand-infos.xml
	dbus-binding-tool --prefix=taskmand --mode=glib-client $<> $@

