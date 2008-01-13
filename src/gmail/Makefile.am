SUBDIRS = Themes

dist_gmail_DATA = 				\
		gmail.py	 			\
		AWN.py

gmaildir = $(libdir)/awn/applets/gmail

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	awngmail.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@


EXTRA_DIST = \
	awngmail.desktop.in.in

