INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"    

HELLOWORLD_SOURCES =                              \
	applet.c									\
	helloworldapplet.c						\
	helloworldapplet.h

HELLOWORLD_LDADD =                        \
        $(DEPS_LIBS)
        

helloworldlibdir = $(libdir)/awn/applets/helloworld
helloworldlib_LTLIBRARIES = helloworld.la
helloworld_la_SOURCES = $(HELLOWORLD_SOURCES)
helloworld_la_LIBADD = $(HELLOWORLD_LDADD)
helloworld_la_LDFLAGS = -module -avoid-version
helloworld_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	helloworld.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	helloworld.desktop.in.in
