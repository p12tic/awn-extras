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
	trash			\
	trasher			\
	$(NULL)
endif
GCONF_APPLETS +=		\
	arss			\
	awn-notification-daemon	\
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
endif
if WITH_GNOME
GCONF_APPLETS +=	\
	main-menu		\
	MiMenu		\
	pandora			\
	rtm	\
	$(NULL)
endif
if WITH_WEBKIT
WEBKIT_APPLETS = \
	webapplet	\
	$(NULL)
endif	

SUBDIRS =			\
	libawn-extras		\
	affinity		\
	awnterm			\
	battery-applet		\
	comics			\
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
	tomboy-applet		\
	volume-control		\
	wobblyzini		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(WEBKIT_APPLETS)	\
	$(NULL)
