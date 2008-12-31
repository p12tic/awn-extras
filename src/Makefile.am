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
GCONF_APPLETS +=		\
	$(NULL)
endif
GCONF_APPLETS +=		\
	awnsystemmonitor	\
	$(NULL)
endif
if WITH_GNOME
GCONF_APPLETS +=	\
	$(NULL)
endif
if WITH_WEBKIT
WEBKIT_APPLETS = \
	$(NULL)
endif
if MAINTAINER_MODE
PYTHON_TEST = 
WOBBLYZINI = 
endif

# please keep alphabetized (except for libawn-extras)
SUBDIRS =			\
	libawn-extras		\
	shiny-switcher		\
	$(WOBBLYZINI)		\
	$(GCONF_APPLETS)	\
	$(VALA_APPLETS)		\
	$(WEBKIT_APPLETS)	\
	$(NULL)
