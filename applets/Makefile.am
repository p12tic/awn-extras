NULL =

CONDITIONAL_APPLETS =

if HAVE_VALA
if MAINTAINER_MODE
CONDITIONAL_APPLETS += maintained/vala-test
endif
if HAVE_LIBZG
CONDITIONAL_APPLETS += maintained/related
endif
CONDITIONAL_APPLETS += \
	maintained/garbage \
	maintained/notification-area \
	maintained/showdesktop \
	$(NULL)
endif

if WITH_GCONF
if WITH_GNOME
# --with-gnome --with-gconf
CONDITIONAL_APPLETS += \
	$(NULL)
endif
# --with-gconf
CONDITIONAL_APPLETS += \
	unmaintained/awnsystemmonitor \
	maintained/calendar \
	maintained/notification-daemon \
	$(NULL)
endif
# --with-gnome
if WITH_GNOME
CONDITIONAL_APPLETS += \
	maintained/cairo-menu \
	unmaintained/main-menu \
	unmaintained/pandora \
	unmaintained/stacks \
	maintained/yama \
	$(NULL)
endif
# --enable-indicator-applet
if ENABLE_INDICATOR
CONDITIONAL_APPLETS += \
	maintained/indicator-applet \
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
CONDITIONAL_APPLETS += unmaintained/dropper
endif

# please keep alphabetized
SUBDIRS = \
	maintained/animal-farm \
	maintained/awnterm \
	maintained/bandwidth-monitor \
	maintained/battery \
	maintained/cairo-clock \
	maintained/comics \
	maintained/cpufreq \
	maintained/dialect \
	maintained/digital-clock \
	maintained/feeds \
	maintained/file-browser-launcher \
	maintained/hardware-sensors \
	maintained/mail \
	maintained/media-control \
	maintained/media-icons \
	maintained/media-player \
	maintained/mount \
	maintained/places \
	maintained/quit \
	maintained/slickswitcher \
	maintained/shiny-switcher \
	maintained/sysmon \
	maintained/thinkhdaps \
	maintained/to-do \
	maintained/tomboy-applet \
	maintained/volume-control \
	maintained/weather \
	$(CONDITIONAL_APPLETS) \
	$(NULL)
# vim: set ts=8 sts=8 sw=8 :
