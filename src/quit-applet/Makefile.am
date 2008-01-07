SUBDIRS = icons

dist_quitapplet_DATA = \
		COPYING	\
		quit-applet.py

quitappletdir = $(libdir)/awn/applets/quit-applet

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	quit-applet.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	quit-applet.desktop.in.in

