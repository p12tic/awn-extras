APPLET_NAME = awnterm
APPLET_CFLAGS = $(VTE_CFLAGS)
VALA_FILES = \
	awn-terminal.vala \
	$(NULL)
AM_VALAFLAGS = --pkg=libintl --pkg=vte --pkg=dbus-glib-1
include $(top_srcdir)/Makefile.vala-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = awnterm.la
awnterm_la_SOURCES =	\
	$(VALA_C_FILES) \
	$(NULL)
awnterm_la_LIBADD =	\
	$(AWN_LIBS)	\
	$(VTE_LIBS)	\
	$(NULL)
awnterm_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
