SUBDIRS = icons

dist_stacksapplet_DATA = \
		stacks_preferences.glade \
		stacks_applet.py \
		stacks_backend.py \
		stacks_backend_file.py \
		stacks_backend_folder.py \
		stacks_backend_plugger.py \
		stacks_backend_trasher.py \
		stacks_config.py \
		stacks_glade.py \
		stacks_gui_curved.py \
		stacks_gui_dialog.py \
		stacks_icons.py \
	    stacks_launcher.py \
		stacks_vfs.py 

stacksappletdir = $(libdir)/awn/applets/stacks

desktopdir = $(libdir)/awn/applets
desktop_DATA = \
	stacks.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	stacks.desktop.in.in

