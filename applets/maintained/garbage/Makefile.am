APPLET_NAME = garbage
VALA_FILES = \
	applet.vala \
	prefs.vala \
	$(NULL)
AM_VALAFLAGS = --pkg=libintl
include $(top_srcdir)/Makefile.vala-applet
include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = garbage.la
garbage_la_SOURCES = \
	$(VALA_C_FILES) \
	$(NULL)
garbage_la_LIBADD = \
	$(AWN_LIBS) \
	$(NULL)
garbage_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
