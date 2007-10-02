SUBDIRS = icons

mediaicon_DATA = \
		COPYING	\
		medialogoplay.py	\
		mediaplayers.py

mediaicondir = $(libdir)/awn/applets/media-icon-play

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	medialogoplay.desktop

@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	medialogoplay.desktop.in.in

