APPLET_NAME = webapplet

include $(top_srcdir)/Makefile.c-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = webapplet.la
webapplet_la_SOURCES = \
	applet.c		\
  applet.h    \
  conf.c      \
  conf.h      \
  engine_webkit.c \
  engine_webkit.h \
  engine_html.c   \
  engine_html.h   \
	$(NULL)
webapplet_la_LIBADD =										\
	$(AWN_LIBS)											\
	$(top_builddir)/src/libawn-extras/libawn-extras.la	\
	$(NULL)
webapplet_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

CFLAGS =    -I/usr/include/WebKit/ \
            -lWebKitGtk

EXTRA_DIST=webapplet.schema-ini
