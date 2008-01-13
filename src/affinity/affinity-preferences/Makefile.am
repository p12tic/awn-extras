glade_DATA = window.glade
gladedir = $(pkgdatadir)

install-exec-local:
	test -d "$(DESTDIR)$(bindir)" || mkdir -p "$(DESTDIR)$(bindir)"
	$(INSTALL) -m 755 affinity-preferences "$(DESTDIR)$(bindir)"

EXTRA_DIST = $(glade_DATA) affinity-preferences.in

clean:
	rm -f *.pyo *.pyc *.bak *.gladep
