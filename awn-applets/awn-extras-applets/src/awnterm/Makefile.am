INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"    

AWNTERM_SOURCES =                                            \
	applet.c

AWNTERM_LDADD =                        \
        $(DEPS_LIBS)
        

awntermlibdir = $(libdir)/awn/applets/awnterm
awntermlib_LTLIBRARIES = awnterm.la
awnterm_la_SOURCES = $(AWNTERM_SOURCES)
awnterm_la_LIBADD = $(AWNTERM_LDADD)
awnterm_la_LDFLAGS = -module -avoid-version
awnterm_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	awnterm.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	awnterm.desktop.in.in
