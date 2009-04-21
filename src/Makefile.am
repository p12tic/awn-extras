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
	cairo-menu		\
	$(NULL)
#	awnsystemmonitor
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
	yama       \
	$(NULL)
endif
if WITH_WEBKIT
WEBKIT_APPLETS = webapplet \
	$(NULL)
endif
if MAINTAINER_MODE
PYTHON_TEST = 
WOBBLYZINI = wobblyzini
endif

# please keep alphabetized (except for libawn-extras)
SUBDIRS =			\
	libawn-extras		\
	animal-farm			\
	awnterm			\
	battery-applet		\
	cairo-clock			\
	cpufreq				\
	gwibfawn		\
	media-player		\
	mount-applet       \
	notification-area	\
	quit-applet			\
	shiny-switcher		\
	showdesktop			\
	thinkhdaps			\
	volume-control		\
	weather				\
	places			\
	$(WOBBLYZINI)		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(WEBKIT_APPLETS)	\
	$(NULL)
