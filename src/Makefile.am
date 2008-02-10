NULL =
if HAVE_VALA
VALA_APPLETS = vala-test standalone-launcher taskmand
endif

GCONF_APPLETS =

if WITH_GCONF
if WITH_GNOME
GCONF_APPLETS +=		\
	awnsystemmonitor	\
	cairo-menu		\
	cairo-menu-classic	\
	calendar		\
	comic			\
	filebrowser		\
	main-menu		\
	plugger			\
	stacks			\
	trash			\
	trasher			\
	$(NULL)
endif
GCONF_APPLETS +=		\
	arss			\
	awn-notification-daemon	\
	awnterm			\
	digitalClock		\
	file-browser-launcher	\
	lastfm			\
	media-control		\
	media-icon-back		\
	media-icon-next		\
	media-icon-play		\
	mount-applet		\
	quit-applet		\
	switcher		\
	weather			\
	$(NULL)
endif
if WITH_GNOME
GCONF_APPLETS +=	\
	digg			\
	MiMenu		\
	pandora			\
	$(NULL)
endif

SUBDIRS =			\
	libawn-extras		\
	affinity		\
	battery-applet		\
	mail			\
	notification-area	\
	places			\
	PyClock			\
	python-test		\
	separator		\
	shiny-switcher		\
	showdesktop		\
	Taskmand-applet		\
	tsclient-applet		\
	volume-control		\
	wobblyzini		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(NULL)
