SUBDIRS = icons

mediaicon_DATA = \
		COPYING	\
		medialogoback.py	\
		medialogonext.py	\
		medialogoplay.py	\
		mediaplayers.py

mediaicondir = $(libdir)/awn/applets/media-icon

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	medialogoplay.desktop	\
	medialogoback.desktop	\
	medialogonext.desktop

@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	medialogoplay.desktop.in.in	\
	medialogoback.desktop.in.in	\
	medialogonext.desktop.in.in

