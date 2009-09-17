APPLET_NAME = showdesktop
APPLET_CFLAGS = $(LIBWNCK_CFLAGS) -I$(top_builddir) -DWNCK_I_KNOW_THIS_IS_UNSTABLE
VALA_FILES = \
	showdesktop.vala	\
	$(NULL)
AM_VALAFLAGS = \
	--pkg libwnck-1.0 \
	--pkg libintl \
	$(NULL)

include $(top_srcdir)/Makefile.vala-applet

applet_LTLIBRARIES = showdesktop.la
showdesktop_la_SOURCES = \
	$(VALA_C_FILES) \
	$(NULL)
showdesktop_la_LIBADD = \
	$(AWN_LIBS) \
	$(LIBWNCK_LIBS) \
	$(NULL)
showdesktop_la_LDFLAGS = $(APPLET_LINKER_FLAGS)

# vim: set ts=8 sts=8 sw=8 :
