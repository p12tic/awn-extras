glade_DATA = window.glade
gladedir = $(pkgdatadir)

desktopdir   = $(datadir)/applications
desktop_DATA = affinity-preferences.desktop
@INTLTOOL_DESKTOP_RULE@


$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@PKGDATADIR\@|$(pkgdatadir)|g" $< > $@

install-exec-local:
	sed -e "s|\@PKGDATADIR\@|$(pkgdatadir)|g" affinity-preferences.in.in.py > affinity-preferences.in.py
	sed -e "s|\@DATADIR\@|$(datadir)|g" affinity-preferences.in.py > affinity-preferences.py
	$(INSTALL) -m 755 affinity-preferences.py $(DESTDIR)$(bindir)/affinity-preferences

EXTRA_DIST = $(glade_DATA) affinity-preferences.in.in.py $(desktop_DATA).in.in

clean:
	rm -f *.pyo *.pyc *.bak *.gladep $(desktop_DATA) $(desktop_DATA).in affinity-preferences.py affinity-preferences.in.py
