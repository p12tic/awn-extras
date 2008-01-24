NULL =
APPLET_NAME = taskmand
SUBDIRS = data

include $(top_srcdir)/Makefile.schemas

INCLUDES =			\
	$(AWN_CFLAGS)		\
	$(TASKMAND_CFLAGS)	\
	$(top_srcdir)/src	\
	$(NULL)

bin_PROGRAMS = taskmand

taskmand_LDADD =						\
	$(AWN_LIBS)						\
	$(TASKMAND_LIBS)					\
	$(top_builddir)/src/libawn-extras/libawn-extras.la	\
	$(NULL)

taskmand_SOURCES =		\
	taskmand.c		\
	taskmand.h		\
	server-bindings.h	\
	$(NULL)

BUILT_SOURCES = server-bindings.h client-bindings.h
# We don't want to install this header
noinst_HEADERS = $(BUILT_SOURCES)

# Correctly clean the generated headers, but keep the xml description
CLEANFILES = $(BUILT_SOURCES)
EXTRA_DIST = taskmand-infos.xml

#Rule to generate the binding headers
server-bindings.h:  taskmand-infos.xml
	dbus-binding-tool --prefix=taskmand --mode=glib-server $<> $@

client-bindings.h:  taskmand-infos.xml
	dbus-binding-tool --prefix=taskmand --mode=glib-client $<> $@


