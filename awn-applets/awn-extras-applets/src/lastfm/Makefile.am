SUBDIRS = icons

dist_volumecontrol_DATA = \
		httpclient.py	\
		lastfm.py	\
		lastfmapplet.py	\
		lastfmconfig.py

volumecontroldir = $(libdir)/awn/applets/lastfm

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	lastfm.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	lastfm.desktop.in.in

