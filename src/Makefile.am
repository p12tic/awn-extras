NULL =
if HAVE_VALA
VALA_APPLETS = vala-test standalone-launcher taskmand simple-launcher
endif

GCONF_APPLETS =

if WITH_GCONF
if WITH_GNOME
GCONF_APPLETS +=		\
	awnsystemmonitor	\
	cairo-menu		\
	cairo-menu-classic	\
	calendar		\
	filebrowser		\
	plugger			\
	stacks			\
	trasher			\
	$(NULL)
endif
GCONF_APPLETS +=		\
	awn-notification-daemon	\
	comic			\
	file-browser-launcher	\
	media-control		\
	media-icon-back		\
	media-icon-next		\
	media-icon-play		\
	mount-applet		\
	weather			\
	$(NULL)
endif
if WITH_GNOME
GCONF_APPLETS +=	\
	main-menu	\
	MiMenu		\
	pandora		\
	rtm		\
	trash		\
	$(NULL)
endif
if WITH_WEBKIT
WEBKIT_APPLETS = \
	webapplet	\
	$(NULL)
endif	

# please keep alphabetized (except for libawn-extras)
SUBDIRS =			\
	libawn-extras		\
	affinity		\
	arss			\
	awnterm			\
	battery-applet		\
	comics			\
	digitalClock		\
	lastfm			\
	mail			\
	notification-area	\
	places			\
	PyClock			\
	python-test		\
	quit-applet		\
	separator		\
	shiny-switcher		\
	showdesktop		\
	switcher		\
	Taskmand-applet		\
	tomboy-applet		\
	tsclient-applet		\
	volume-control		\
	wobblyzini		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(WEBKIT_APPLETS)	\
	$(NULL)
