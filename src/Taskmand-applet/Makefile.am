APPLET_NAME = Taskmand-applet

include $(top_srcdir)/Makefile.c-applet


applet_LTLIBRARIES = Taskmand-applet.la
Taskmand_applet_la_SOURCES = \
	applet.c		\
	$(NULL)
Taskmand_applet_la_LIBADD =										\
	$(AWN_LIBS)											\
	$(NULL)
Taskmand_applet_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
