dist_blingswitcher_DATA = 				\
		PySwitcher.py 			\
		CairoWidgets_BlingSwitcher.py	\
		BlingSwitcher.png
blingswitcherdir = $(libdir)/awn/applets/BlingSwitcher

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	PySwitcher.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	PySwitcher.desktop.in.in

