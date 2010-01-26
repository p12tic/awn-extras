APPLET_NAME = dialect
APPLET_MAIN_FILE = dialect.py

include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA =  \
	dialect.ui  \
	$(NULL)

dialect_iconsdir = $(applet_datadir)/icons
dist_dialect_icons_DATA =	\
	$(wildcard icons/*.png) \
	$(NULL)
