INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(AWN_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                  \
	-I$(top_builddir)/libawn

WOBBLYZINI_SOURCES =                              \
	applet.c									\
	wobblyziniapplet.c						\
	wobblyziniapplet.h

WOBBLYZINI_LDADD =                        \
        $(DEPS_LIBS)			        \
        $(AWN_LIBS)                             \
        $(top_builddir)/libawn/libawn.la
        

wobblyzinilibdir = $(libdir)/awn/applets/wobblyzini
wobblyzinilib_LTLIBRARIES = wobblyzini.la
wobblyzini_la_SOURCES = $(WOBBLYZINI_SOURCES)
wobblyzini_la_LIBADD = $(WOBBLYZINI_LDADD)
wobblyzini_la_LDFLAGS = -module -avoid-version 
wobblyzini_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	wobblyzini.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	wobblyzini.desktop.in.in
