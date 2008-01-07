SUBDIRS = Core

dist_arss_DATA = \
		rss_awn.py \
		COPYING \
		README

arssdir = $(libdir)/awn/applets/arss

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	arss.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	arss.desktop.in.in

