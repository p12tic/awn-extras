APPLET_NAME = indicator-applet

APPLET_CFLAGS = $(INDICATOR_CFLAGS) \
	-DINDICATOR_DIR=\""$(INDICATORDIR)"\" \
	$(NULL)

include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = indicator-applet.la
indicator_applet_la_SOURCES =		\
	applet.c		\
	$(NULL)
indicator_applet_la_LIBADD =						\
	$(AWN_LIBS)						\
	$(INDICATOR_LIBS)			\
	$(NULL)
indicator_applet_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
