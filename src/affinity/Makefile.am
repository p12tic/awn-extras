SUBDIRS = affinity-preferences data
APPLET_NAME = affinity
APPLET_CFLAGS =						\
	$(AFFINITY_CFLAGS)				\
	-DACTIONDIR=\""$(datadir)/affinity/actions"\"	\
	$(NULL)
include $(top_srcdir)/Makefile.c-applet

applet_LTLIBRARIES = affinity.la

affinity_la_SOURCES =			\
	applet.c			\
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
	tomboykeybinder.h		\
	$(NULL)

if !LIBAWN_USE_GNOME
affinity_la_SOURCES +=		\
	egg-pixbuf-thumbnail.c	\
	egg-pixbuf-thumbnail.h	\
	$(NULL)
endif

BEAGLE_SOURCES =			\
	aff-search-engine-beagle.c	\
	aff-search-engine-beagle.h	\
	$(NULL)

if HAVE_BEAGLE
affinity_la_SOURCES += $(BEAGLE_SOURCES)
endif

TRACKER_SOURCES = \
	aff-search-engine-tracker.c \
	aff-search-engine-tracker.h

if HAVE_TRACKER
affinity_la_SOURCES += $(TRACKER_SOURCES)
endif
	
affinity_la_LIBADD =		\
	$(AWN_LIBS)		\
	$(AFFINITY_LIBS)	\
	$(NULL)
affinity_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

EXTRA_DIST=po/Makefile.in.in
