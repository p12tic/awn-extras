SUBDIRS = Themes

volumecontrol_DATA = volume-control.py
volumecontroldir = $(libdir)/awn/applets/volume-control

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	volume-control.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	volume-control.desktop.in.in

