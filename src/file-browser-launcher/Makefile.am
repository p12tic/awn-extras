file_browser_launcher_DATA = 				\
		about.py	\
		file-browser-launcher.py	\
		prefs.py		\
		gconfwrapper.py
		
file_browser_launcherdir = $(libdir)/awn/applets/file-browser-launcher


desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	file-browser-launcher.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	file-browser-launcher.desktop.in.in

