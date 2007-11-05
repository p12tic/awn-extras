SUBDIRS = Themes

dist_pyclock_DATA = \
		PyClock.py	\
		PyClock.png

pyclockdir = $(libdir)/awn/applets/PyClock

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	PyClock.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	PyClock.desktop.in.in

