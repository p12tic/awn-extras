APPLET_NAME = sysmon
APPLET_CFLAGS = \
	$(GTOP_CFLAGS) \
	-std=c99 \
	-D_GNU_SOURCE \
	$(NULL)
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
  cpuicon.h \
  defines.h \
  graph.c \
  graph.h \
  graphprivate.h \
  loadicon.c \
  loadicon.h \
  piegraph.c \
  piegraph.h \
  sysmon.c  \
  sysmon.h  \
  sysmonicon.c \
  sysmonicon.h \
  sysmoniconprivate.h \
  util.c  \
  util.h  \
  $(NULL)
sysmon_la_LIBADD = \
	$(AWN_LIBS) \
	$(GTOP_LIBS) \
	$(NULL)

sysmon_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

