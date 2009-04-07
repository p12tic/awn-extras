SUBDIRS =				\
	src						\
	po
	
EXTRA_DIST =				\
	intltool-extract.in		\
	intltool-merge.in		\
	intltool-update.in		\
	po/Makefile.in.in \
	po/POTFILES.skip \
	autogen.sh

DISTCLEANFILES =			\
	intltool-extract		\
	intltool-merge			\
	intltool-update

ACLOCAL_AMFLAGS = -I m4

gtk_update_icon_cache = gtk-update-icon-cache -f -t ${datadir}/icons/hicolor

install-data-hook: update-icon-cache
uninstall-hook: update-icon-cache

update-icon-cache:
	@-if test -z "$(DESTDIR)"; then \
		echo "Updating Gtk icon cache."; \
		$(gtk_update_icon_cache); \
	else \
		echo "*** Icon cache not updated.  After install, run this:"; \
		echo "***   $(gtk_update_icon_cache)"; \
	fi
