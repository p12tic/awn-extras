

dist_pandora_DATA = \
		awn-pandora.py	\
		pandora.ico
		
pandoradir = $(libdir)/awn/applets/pandora

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	awn-pandora.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	awn-pandora.desktop.in.in

