SUBDIRS = icons

INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"    

WOBBLYZINI_SOURCES =                              \
	applet.c									\
	wobblyziniapplet.c						\
	wobblyziniapplet.h

WOBBLYZINI_LDADD =                        \
        $(DEPS_LIBS)
        

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
