INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"    

CPUMETER_SOURCES =                              \
	applet.c									\
	cpumeterapplet.c						\
	cpumeterapplet.h

CPUMETER_LDADD =                        \
        $(DEPS_LIBS)
        

cpumeterlibdir = $(libdir)/awn/applets/cpumeter
cpumeterlib_LTLIBRARIES = cpumeter.la
cpumeter_la_SOURCES = $(CPUMETER_SOURCES)
cpumeter_la_LIBADD = $(CPUMETER_LDADD)
cpumeter_la_LDFLAGS = -module -avoid-version
cpumeter_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	cpumeter.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	cpumeter.desktop.in.in
