SUBDIRS = icons

stacksapplet_DATA = \
		stacks_preferences.glade \ 
		stacks.py \
		stacksbackend.py \
	    stacksconfig.py \
		stacksglade.py \
		stacksicons.py \
	    stackslauncher.py \
		stacksvfs.py

stacksappletdir = $(libdir)/awn/applets/stacks

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	stacks.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	stacks.desktop.in.in

