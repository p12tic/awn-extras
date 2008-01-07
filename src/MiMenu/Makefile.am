SUBDIRS = icons

dist_quitapplet_DATA = \
		COPYING	\
		keyboard.py	\
		menus.py	\
		mimenu.py	\
		pathfinder.py

quitappletdir = $(libdir)/awn/applets/MiMenu

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	mimenu.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	mimenu.desktop.in.in

