INCLUDES =							\
	-I$(srcdir)						\
	-I/usr/include/librsvg-2				\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(AWN_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                  \
	-I$(top_builddir)/libawn

CLOCK_SOURCES =                              \
	applet.c				\
	clock-applet.h				\
	clock-applet.c				\
	utils.c					\
	utils.h

CLOCK_LDADD =                        \
        $(DEPS_LIBS)			        \
        $(AWN_LIBS)                             \
        $(top_builddir)/libawn/libawn.la
        

clocklibdir = $(libdir)/awn/applets/clock
clocklib_LTLIBRARIES = clock.la
clock_la_SOURCES = $(CLOCK_SOURCES)
clock_la_LIBADD = $(CLOCK_LDADD)
clock_la_LDFLAGS = -module -avoid-version 
clock_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	clock.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	clock.desktop.in.in
