APPLET_NAME = standalone-launcher

# stop-gap until there's real vala support in automake.
VALA_FILES =	\
	applet.vala	\
	$(NULL)
APPLET_CFLAGS =				\
	-DWNCK_I_KNOW_THIS_IS_UNSTABLE	\
	-std=c99			\
	$(NULL)
AM_VALAFLAGS = --pkg=libwnck-1.0 --pkg=dbus-glib-1
AM_LDFLAGS = -lm
include $(top_srcdir)/Makefile.vala-applet
include $(top_srcdir)/Makefile.schemas
