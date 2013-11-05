APPLET_NAME = awnterm
APPLET_CFLAGS = $(VTE_CFLAGS)
VALAC = valac-0.12
VALA_FILES = \
	awn-terminal.vala \
	$(NULL)
AM_VALAFLAGS = \
	--pkg=libintl \
	--pkg=vte \
	--pkg=dbus-glib-1 \
	$(srcdir)/keybinder.vapi \
	$(NULL)

include $(top_srcdir)/Makefile.vala-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = awnterm.la
awnterm_la_SOURCES =	\
	$(VALA_C_FILES) \
	eggaccelerators.c \
	eggaccelerators.h \
	keybinder.c \
	keybinder.h \
	$(NULL)
awnterm_la_LIBADD =	\
	$(AWN_LIBS)	\
	$(VTE_LIBS)	\
	$(NULL)
awnterm_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

EXTRA_DIST += keybinder.vapi

