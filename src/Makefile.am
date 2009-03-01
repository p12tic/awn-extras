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
	awn-notification-daemon \
	$(NULL)
endif
# --with-gnome
if WITH_GNOME
GCONF_APPLETS +=	\
	main-menu	\
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
	awnterm			\
	media-player		\
	notification-area	\
	shiny-switcher		\
	places			\
	$(WOBBLYZINI)		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(WEBKIT_APPLETS)	\
	$(NULL)
