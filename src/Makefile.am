NULL =
if HAVE_VALA
if MAINTAINER_MODE
VALA_TEST = vala-test
endif
VALA_APPLETS = $(VALA_TEST) taskmand simple-launcher standalone-launcher Taskmand-applet 
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
	media-control		\
	mount-applet		\
	$(NULL)
endif
if WITH_GNOME
GCONF_APPLETS +=	\
	digg		\
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
if MAINTAINER_MODE
PYTHON_TEST = python-test
WOBBLYZINI = wobblyzini
endif

# please keep alphabetized (except for libawn-extras)
SUBDIRS =			\
	libawn-extras		\
	affinity		\
	animal-farm		\
	arss			\
	awn-meebo		\
	awnterm			\
	battery-applet		\
	cairo-clock		\
	comic			\
	comics			\
	cpufreq			\
	DesktopManager		\
	digitalClock		\
	file-browser-launcher	\
	lastfm			\
	mail			\
	media-icon-back		\
	media-icon-next		\
	media-icon-play		\
	media-player		\
	notification-area	\
	places			\
	pynot				\
	pynot-rgba		\
	$(PYTHON_TEST)		\
	quit-applet		\
	separator		\
	shiny-switcher		\
	showdesktop		\
	switcher		\
	thinkhdaps			\
	to-do				\
	tomboy-applet		\
	volume-control		\
	weather			\
	$(WOBBLYZINI)		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(WEBKIT_APPLETS)	\
	$(NULL)
