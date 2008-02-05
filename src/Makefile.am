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
	clock			\
	comic			\
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
else
if WITH_GNOME
GCONF_APPLETS +=	\
	MiMenu		\
	$(NULL)
endif
endif

SUBDIRS =			\
	libawn-extras		\
	affinity		\
	battery-applet		\
	comic			\
	digg			\
	mail			\
	notification-area	\
	pandora			\
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
