SUBDIRS = icons

mediacontrol_DATA = \
		mediacontrol.py	\
		mediaplayers.py	\
		noArtIcon.png	\
		COPYING
		
mediacontroldir = $(libdir)/awn/applets/media-control

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	media-control.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	media-control.desktop.in.in

