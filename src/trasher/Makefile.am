INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)				\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                  

TRASHER_SOURCES =                              \
	applet.c

TRASHER_LDADD =                        \
        $(DEPS_LIBS)			        
        

trasherlibdir = $(libdir)/awn/applets/trasher
trasherlib_LTLIBRARIES = trasher.la
trasher_la_SOURCES = $(TRASHER_SOURCES)
trasher_la_LIBADD = $(TRASHER_LDADD)
trasher_la_LDFLAGS = -module -avoid-version
trasher_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	trasher.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	trasher.desktop.in.in
