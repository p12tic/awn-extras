INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(AWN_CFLAGS)					\
	$(FILEBROWSER_CFLAGS)			\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                  

FILEBROWSER_SOURCES =                              \
	filebrowser-applet.c \
	filebrowser-applet.h \
	filebrowser-defines.h \
	filebrowser-dialog.c \
	filebrowser-dialog.h \
	filebrowser-folder.c \
	filebrowser-folder.h \
	filebrowser-gconf.c \
	filebrowser-gconf.h \
	filebrowser-icon.c \
	filebrowser-icon.h \
	filebrowser-utils.c \
	filebrowser-utils.h

FILEBROWSER_LDADD =                        \
        $(AWN_LIBS)							\
		$(FILEBROWSER_LIBS)

filebrowserlibdir = $(libdir)/awn/applets/filebrowser/
filebrowserlib_LTLIBRARIES = filebrowser.la
filebrowser_la_SOURCES = $(FILEBROWSER_SOURCES)
filebrowser_la_LIBADD = $(FILEBROWSER_LDADD)
filebrowser_la_LDFLAGS = -module -avoid-version
filebrowser_la_CFLAGS =

schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_FILE = filebrowser.schemas
schemas_in_files = $(schemas_FILE).in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)
	
@INTLTOOL_SCHEMAS_RULE@
	
if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif

icondir = $(pkgdatadir)

icon_DATA =  \
	filebrowser.svg

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	filebrowser.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA): $(desktop_DATA).in
	sed -e "s|\@LIBDIR\@|$(libdir)|g;s|\@ICONDIR\@|$(icondir)|g" $< > $@

EXTRA_DIST = \
	$(icon_DATA) \
	$(desktop_DATA).in \
	$(schemas_in_files)
	
CLEANFILES = $(desktop_DATA) filebrowser.schemas	
