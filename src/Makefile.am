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
# --with-gnome --with-gconf
GCONF_APPLETS +=		\
	awnsystemmonitor	\
	cairo-menu		\
	calendar		\
	filebrowser		\
	plugger			\
	stacks			\
	trasher			\
	$(NULL)
endif
# --with-gconf
GCONF_APPLETS +=		\
	awn-notification-daemon	\
	media-control		\
	$(NULL)
endif
# --with-gnome
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
	mail			\
	media-icon-back		\
	media-icon-next		\
	media-icon-play		\
	media-player		\
	mount-applet       \
	notification-area	\
	places			\
	pynot				\
	pynot-rgba		\
	$(PYTHON_TEST)		\
	quit-applet		\
	separator		\
	shiny-switcher		\
	showdesktop		\
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
