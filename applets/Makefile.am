NULL =

CONDITIONAL_APPLETS =

if HAVE_VALA
if MAINTAINER_MODE
CONDITIONAL_APPLETS += maintained/vala-test
endif
#uncomment once lda's vapi files have fixed header definitions
#CONDITIONAL_APPLETS += maintained/notification-area
endif

if WITH_GCONF
if WITH_GNOME
# --with-gnome --with-gconf
CONDITIONAL_APPLETS += \
	maintained/awnsystemmonitor \
	maintained/cairo-menu \
	$(NULL)
endif
# --with-gconf
CONDITIONAL_APPLETS += \
	maintained/calendar \
	maintained/media-control \
	maintained/notification-daemon \
	$(NULL)
endif
# --with-gnome
if WITH_GNOME
CONDITIONAL_APPLETS += \
	unmaintained/main-menu \
	unmaintained/MiMenu \
	unmaintained/pandora \
	maintained/yama \
	$(NULL)
endif
# --with-webkit and/or --with-mozilla
if BUILD_WEBAPPLET
CONDITIONAL_APPLETS += \
	maintained/webapplet \
	$(NULL)
endif
if MAINTAINER_MODE
CONDITIONAL_APPLETS += maintained/python-test
CONDITIONAL_APPLETS += maintained/wobblyzini
endif

# please keep alphabetized
SUBDIRS = \
	maintained/animal-farm \
	maintained/awnterm \
	maintained/battery \
	maintained/cairo-clock \
	maintained/cpufreq \
	maintained/feeds \
	maintained/file-browser-launcher \
	maintained/gwibfawn \
	unmaintained/mail \
	maintained/media-icons \
	maintained/media-player \
	maintained/mount-applet \
	maintained/places \
	maintained/quit \
	maintained/shiny-switcher \
	maintained/showdesktop \
	maintained/sysmon \
	maintained/thinkhdaps \
	maintained/to-do \
	maintained/tomboy-applet \
	maintained/volume-control \
	maintained/weather \
	$(CONDITIONAL_APPLETS) \
	$(NULL)
# vim: set ts=8 sts=8 sw=8 :
