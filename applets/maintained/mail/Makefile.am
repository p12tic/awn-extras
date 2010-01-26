APPLET_NAME = mail
APPLET_MAIN_FILE = mail.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas
dist_applet_DATA = 		\
    mail.ui \
    $(NULL)

theme_gmaildir = $(applet_datadir)/themes/GMail
dist_theme_gmail_DATA =			\
	themes/GMail/index.theme	\
	$(NULL)
	
iconsdir = $(applet_datadir)/icons
dist_icons_DATA =		\
	icons/error.svg	\
	icons/login.svg	\
	icons/read.svg		\
	icons/unread.svg	\
	$(NULL)

theme_gmail_scalabledir = $(applet_datadir)/themes/GMail/scalable
dist_theme_gmail_scalable_DATA =		\
	themes/GMail/scalable/error.svg		\
	themes/GMail/scalable/login.svg		\
	themes/GMail/scalable/read.svg		\
	themes/GMail/scalable/unread.svg	\
	$(NULL)

theme_reserveddir = $(applet_datadir)/themes/Reserved
dist_theme_reserved_DATA =		\
	themes/Reserved/index.theme	\
	$(NULL)

theme_reserved_scalabledir = $(applet_datadir)/themes/Reserved/scalable
dist_theme_reserved_scalable_DATA =		\
	themes/Reserved/scalable/error.svg	\
	themes/Reserved/scalable/login.svg	\
	themes/Reserved/scalable/read.svg	\
	themes/Reserved/scalable/unread.svg	\
	$(NULL)
