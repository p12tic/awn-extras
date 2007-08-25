INCLUDES =							\
	-I$(srcdir)						\
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\"		\
	$(DISABLE_DEPRECATED_CFLAGS)				\
	$(DEPS_CFLAGS)					\
	-DPREFIX=\"$(prefix)\"					\
	-DSYSCONFDIR=\"$(sysconfdir)\"				\
	-DDATADIR=\"$(datadir)\"				\
	-DLIBDIR=\"$(libdir)\"                                  \
	-I$(top_builddir)/libawn

STACK_SOURCES =                              \
	applet.c     \
	stack-applet.c                           \
	stack-cairo.c \
	stack-dialog.c \
	stack-gconf.c \
	stack-icon.c \
	stack-pixbuf-utils.c \
	stack-folder.c

STACK_LDADD =                        \
        $(DEPS_LIBS)			        \
        $(AWN_LIBS)

stacklibdir = $(libdir)/awn/applets/stack/
stacklib_LTLIBRARIES = stack.la
stack_la_SOURCES = $(STACK_SOURCES)
stack_la_LIBADD = $(STACK_LDADD)
stack_la_LDFLAGS = -module -avoid-version
stack_la_CFLAGS =

schemasdir   = @GCONF_SCHEMA_FILE_DIR@
schemas_in_files = stack.schemas.in
schemas_DATA = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schemas_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
endif


desktopdir = $(libdir)/awn/applets

desktop_DATA = \
	stack.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA): $(desktop_DATA).in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	stack.desktop.in \
	$(schemas_in_files)
