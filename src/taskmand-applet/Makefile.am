APPLET_NAME = taskmand-applet

include $(top_srcdir)/Makefile.c-applet


applet_LTLIBRARIES = taskmand-applet.la
taskmand_applet_la_SOURCES = \
	applet.c		\
	$(NULL)
taskmand_applet_la_LIBADD =										\
	$(AWN_LIBS)											\
	$(NULL)
taskmand_applet_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
