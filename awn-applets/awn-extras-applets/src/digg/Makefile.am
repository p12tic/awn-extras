SUBDIRS = profile

dist_digg_DATA = \
		awn-digg.py	\
		digg.png

diggdir = $(libdir)/awn/applets/digg

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	awn-digg.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	awn-digg.desktop.in.in

