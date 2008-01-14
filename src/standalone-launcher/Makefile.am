APPLET_NAME = standalone-launcher

# stop-gap until there's real vala support in automake.
VALA_FILES =	\
	applet.vala	\
	$(NULL)
APPLET_CFLAGS =				\
	-DWNCK_I_KNOW_THIS_IS_UNSTABLE	\
	$(STANDALONE_LAUNCHER_CFLAGS)	\
	$(NULL)
AM_VALAFLAGS = --pkg=libwnck-1.0 --pkg=dbus-glib-1
include $(top_srcdir)/Makefile.vala-applet


include $(top_srcdir)/Makefile.schemas


applet_LTLIBRARIES = standalone-launcher.la
standalone_launcher_la_SOURCES =	\
	$(GENERATED_C_FILES)	\
	$(GENERATED_H_FILES)	\
	$(NULL)
standalone_launcher_la_LIBADD =		\
	$(AWN_LIBS)			\
	$(STANDALONE_LAUNCHER_LIBS)	\
	$(NULL)
standalone_launcher_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
