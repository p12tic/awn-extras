SUBDIRS = icons

dist_mediaiconback_DATA = \
		COPYING	\
		medialogoback.py	\
		mediaplayers.py

mediaiconbackdir = $(libdir)/awn/applets/media-icon-back

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	medialogoback.desktop

@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	medialogoback.desktop.in.in

