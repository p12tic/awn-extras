APPLET_NAME = places

include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = places.la
places_la_SOURCES =		\
	applet.c		\
	$(NULL)
places_la_LIBADD =						\
	$(AWN_LIBS)						\
	$(top_builddir)/src/libawn-extras/libawn-extras.la	\
	$(NULL)
places_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
