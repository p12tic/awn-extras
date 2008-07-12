NULL =
if HAVE_VALA
VALA_APPLETS = vala-test taskmand simple-launcher Taskmand-applet
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
	media-control		\
	mount-applet		\
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
	awn-meebo		\
	awnterm			\
	battery-applet		\
	cairo-clock		\
	comics			\
	digitalClock		\
	file-browser-launcher \
	lastfm			\
	mail			\
	media-icon-back		\
	media-icon-next		\
	media-icon-play		\
	notification-area	\
	places			\
        pynot                   \
	python-test		\
	quit-applet		\
	separator		\
	shiny-switcher		\
	showdesktop		\
	switcher		\
	thinkhdaps			\
	to-do				\
	tomboy-applet		\
	tsclient-applet		\
	volume-control		\
	weather			\
	wobblyzini		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(WEBKIT_APPLETS)	\
	$(NULL)
