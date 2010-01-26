APPLET_NAME = stacks
APPLET_MAIN_FILE = stacks_applet.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA =			\
	stacks_preferences.glade	\
	curved_stacks_preferences.glade	\
	stacks_backend.py		\
	stacks_backend_file.py		\
	stacks_backend_folder.py	\
	stacks_backend_plugger.py	\
	stacks_backend_trasher.py	\
	stacks_config.py		\
	stacks_glade.py			\
	stacks_gui_curved.py		\
	stacks_gui_dialog.py		\
	stacks_gui_trasher.py		\
	stacks_icons.py			\
	stacks_launcher.py		\
	stacks_vfs.py			\
	$(NULL)

stacks_iconsdir = $(applet_datadir)/icons
dist_stacks_icons_DATA = 	\
	icons/stacks-drop.svg	\
	icons/stacks-full.svg	\
	$(NULL)
