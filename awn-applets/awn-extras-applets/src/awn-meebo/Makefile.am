SUBDIRS = profile

dist_meebo_DATA = \
		awn-meebo.py	\
		meebo.png

meebodir = $(libdir)/awn/applets/awn-meebo

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	awn-meebo.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	awn-meebo.desktop.in.in

