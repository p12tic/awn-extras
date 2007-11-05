SUBDIRS = icons

dist_tsclient_DATA = tsclient_app.py

tsclientdir = $(libdir)/awn/applets/tsclient-applet

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	tsclient-app.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	tsclient-app.desktop.in.in

