SUBDIRS = google images

dist_gmail_DATA = 				\
		calendarlogin.py 			\
		calendarprefs.py		\
		clockcal.py		\
		calthread.py	\
		evocal.py	\
		googlecal.py	\
		icscal.py	\
		owacal.py	\
		sevensegled.py

gmaildir = $(libdir)/awn/applets/calendar

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	calendar.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	calendar.desktop.in.in

