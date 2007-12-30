INCLUDES = \
	-I$(srcdir) \
	-DGNOMELOCALEDIR=\""$(datadir)/locale"\" \
	$(DISABLE_DEPRECATED_CFLAGS) \
	$(DEPS_CFLAGS) \
	-DPREFIX=\"$(prefix)\" \
	-DSYSCONFDIR=\"$(sysconfdir)\" \
	-DACTIONDIR=\""$(datadir)/affinity/actions"\"  \
	-DDATADIR=\"$(datadir)\" \
	-DLIBDIR=\"$(libdir)\" \
	$(TRACKER_CFLAGS) \
	$(BEAGLE_CFLAGS) \
	$(APPLET_CFLAGS)

affinity_SOURCES = 	\
	applet.c				\
	affinity.c      		\
	affinity.h	        	\
	aff-button.c	        	\
	aff-button.h	        	\
	aff-results.c	        	\
	aff-results.h	        	\
	aff-search-engine.c             \
	aff-search-engine.h             \
	aff-search-engine-actions.c     \
	aff-search-engine-actions.h     \
	aff-search-engine-apps.c        \
	aff-search-engine-apps.h        \
	aff-settings.c	        	\
	aff-settings.h		        \
	aff-sidebar.c		        \
	aff-sidebar.h		        \
	aff-start.c		        \
	aff-start.h		        \
	aff-utils.c                     \
	aff-utils.h                     \
	aff-window.c		        \
	aff-window.h			\
	eggaccelerators.c		\
	eggaccelerators.h		\
	tomboykeybinder.c		\
	tomboykeybinder.h		

BEAGLE_SOURCES = \
	aff-search-engine-beagle.c \
	aff-search-engine-beagle.h

if HAVE_BEAGLE
affinity_SOURCES += $(BEAGLE_SOURCES)
endif

TRACKER_SOURCES = \
	aff-search-engine-tracker.c \
	aff-search-engine-tracker.h

if HAVE_TRACKER
affinity_SOURCES += $(TRACKER_SOURCES)
endif
	
affinity_LDADD  = \
	$(DEPS_LIBS) $(BEAGLE_LIBS) $(TRACKER_LIBS)

affinitylibdir = $(libdir)/awn/applets/affinity
affinitylib_LTLIBRARIES = affinity.la
affinity_la_SOURCES = $(affinity_SOURCES)
affinity_la_LIBADD = $(affinity_LDADD)
affinity_la_LDFLAGS = -module -avoid-version
affinity_la_CFLAGS =

desktopdir = $(libdir)/awn/applets

desktop_DATA = \
		affinity.desktop
@INTLTOOL_DESKTOP_RULE@

$(desktop_DATA).in: $(desktop_DATA).in.in
	sed -e "s|\@LIBDIR\@|$(libdir)|g" $< > $@

EXTRA_DIST = \
	affinity.desktop.in.in


MAINTAINERCLEANFILES = aclocal.m4 compile config.guess config.sub configure depcomp install-sh ltmain.sh Makefile.in missing

