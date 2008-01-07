SUBDIRS = icons

dist_mediaicon_DATA = \
		COPYING	\
		medialogonext.py	\
		mediaplayers.py

mediaicondir = $(libdir)/awn/applets/media-icon-next

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	medialogonext.desktop

@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	medialogonext.desktop.in.in

