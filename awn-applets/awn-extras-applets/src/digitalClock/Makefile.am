dist_volumecontrol_DATA = \
		dgClockPref.py	\
		dgTime.py	\
		digitalClock.py	\
		pref.glade

volumecontroldir = $(libdir)/awn/applets/digitalClock

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	digitalClock.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	digitalClock.desktop.in.in

