SUBDIRS = images

weather_DATA = 				\
		weather.py		\
		messages.pot		\
		weatherconfig.py	\
		weatherdialog.py	\
		weathericons.py		\
		weathercurved.py	\
		weathertext.py		\
		weathermap.py		\
		override.py
		
weatherdir = $(libdir)/awn/applets/weather

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	weather.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	weather.desktop.in.in

