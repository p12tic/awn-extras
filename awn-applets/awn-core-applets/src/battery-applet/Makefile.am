SUBDIRS = icons

batteryapplet_DATA = \
		battery-applet.py \
		COPYING

batteryappletdir = $(libdir)/awn/applets/volume-control

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	battery-applet.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	battery-applet.desktop.in.in

