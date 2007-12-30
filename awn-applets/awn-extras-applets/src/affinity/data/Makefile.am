SUBDIRS = actions 16x16 22x22 24x24 48x48 scalable

desktopdir   = $(datadir)/applications
desktop_DATA = affinity.desktop
@INTLTOOL_DESKTOP_RULE@

serverdir   = $(libdir)/bonobo/servers
server_DATA = GNOME_Affinity.server
@INTLTOOL_SERVER_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@PKGDATADIR\@|$(pkgdatadir)|g" $< > $@

$(server_DATA).in: $(server_DATA).in.in
	sed -e "s|\@LIBEXECDIR\@|$(libexecdir)|" $< > $@

EXTRA_DIST = $(desktop_DATA).in.in $(server_DATA).in.in

clean:
	rm -f $(desktop_DATA) $(desktop_DATA).in $(server_DATA) $(server_DATA).in	
