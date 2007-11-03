dist_test_DATA = showdesktop.py
testdir = $(libdir)/awn/applets/showdesktop

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	showdesktop.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	showdesktop.desktop.in.in

