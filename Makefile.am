NULL =
SUBDIRS = \
	applets \
	shared/python \
	shared/vala \
	po \
	$(NULL)
	
EXTRA_DIST = \
	autogen.sh \
	intltool-extract.in \
	intltool-merge.in \
	intltool-update.in \
	po/Makefile.in.in \
	po/POTFILES.skip \
	COPYING.BSD \
	COPYING.CCASAv3.0 \
	COPYING.GPL-3 \
	COPYING.LGPL-2.1 \
	$(NULL)

DISTCLEANFILES =			\
	intltool-extract		\
	intltool-merge			\
	intltool-update

ACLOCAL_AMFLAGS = -I m4

DISTCHECK_CONFIGURE_FLAGS = --disable-pymod-checks

i18n-update: po/POTFILES.in po/POTFILES.skip
	(cd po && for lang in `grep ALL_LINGUAS ../configure.ac | cut -d'"' -f2`; do \
		echo -n "Updating $$lang:"; \
		intltool-update $$lang; \
	done)

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
