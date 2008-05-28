SUBDIRS = . bindings
lib_LTLIBRARIES = libawn-extras.la

AM_CFLAGS =			\
	$(AWN_CFLAGS)		\
	$(LIBNOTIFY_CFLAGS)	\
	-I$(top_srcdir) 	\
	-I$(top_builddir) 	\
	$(NULL)

libawn_extrasincdir = $(includedir)/libawn-extras

source_h =	\
	awn-extras.h
	
source_c =	\
	colour.c	\
	pixbufs.c	\
	url.c		\
	notify.c    \
	config_shared.c \
	shared_menus.c
	
libawn_extrasinc_HEADERS = \
	$(source_h)
	
libawn_extras_la_SOURCES = \
	$(source_c)
	
libawn_extras_la_LIBADD = $(AWN_LIBS) $(LIBNOTIFY_LIBS)
libawn_extras_la_LDFLAGS = -version-info 0:1:0
