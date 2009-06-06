APPLET_NAME = sysmon
APPLET_CFLAGS = $(AWN_SYSTEM_MONITOR_CFLAGS)
include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = sysmon.la
sysmon_la_SOURCES =		\
  applet.c  \
  areagraph.c \
  areagraph.h \
  bargraph.c \
  bargraph.h \
  circlegraph.c \
  circlegraph.h \
  cpu-dialog.c \
  cpu-dialog.h \
  cpuicon.c \
  cupicon.h \
  defines.h \
  graph.c \
  graph.h \
  loadicon.c \
  loadicon.h \
  piegraph.c \
  piegraph.h \
  sysmon.c  \
  sysmon.h  \
  sysmonicon.c \
  sysmonicon.h \
  util.c  \
  util.h  \
  $(NULL)
sysmon_la_LIBADD =					\
	$(AWN_LIBS)						\
	$(top_builddir)/src/libawn-extras/libawn-extras.la	\
	$(AWN_SYSTEM_MONITOR_LIBS)				\
	$(NULL)

sysmon_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

