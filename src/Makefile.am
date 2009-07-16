NULL =
if HAVE_VALA
if MAINTAINER_MODE
VALA_TEST = vala-test
endif
VALA_APPLETS =  
endif

GCONF_APPLETS =

if WITH_GCONF
if WITH_GNOME
# --with-gnome --with-gconf
GCONF_APPLETS +=		\
	awnsystemmonitor	\
	cairo-menu		\
	$(NULL)
endif
# --with-gconf
GCONF_APPLETS +=		\
	awn-notification-daemon	\
	calendar		\
	media-control		\
	$(NULL)
endif
# --with-gnome
if WITH_GNOME
GCONF_APPLETS +=	\
	main-menu	\
	MiMenu		\
	pandora		\
	yama       \
	$(NULL)
endif
# --with-webkit and/or --with-mozilla
if BUILD_WEBAPPLET
WEBAPPLET =		\
	webapplet	\
	$(NULL)
endif
if MAINTAINER_MODE
PYTHON_TEST = 
WOBBLYZINI = wobblyzini
endif

# please keep alphabetized
SUBDIRS =			\
	animal-farm			\
	awnterm			\
	battery-applet		\
	cairo-clock			\
	cpufreq				\
	file-browser-launcher	\
	gwibfawn		\
	mail			\
	media-icons		\
	media-player		\
	mount-applet       \
	notification-area	\
	places			\
	quit-applet			\
	shiny-switcher		\
	showdesktop			\
	sysmon			\
	thinkhdaps			\
	to-do			\
	tomboy-applet			\
	volume-control		\
	weather				\
	$(WOBBLYZINI)		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(WEBAPPLET)		\
	$(NULL)
