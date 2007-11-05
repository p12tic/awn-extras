SUBDIRS = images

dist_volumecontrol_DATA = \
		comic.py	\
		comicdialog.py	\
		getborn.py	\
		getdilbert.py	\
		getpcnp.py	\
		getpeanuts.py	\
		getwiz.py

volumecontroldir = $(libdir)/awn/applets/comic

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	comic.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	comic.desktop.in.in

