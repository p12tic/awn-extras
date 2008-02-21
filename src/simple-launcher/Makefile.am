APPLET_NAME = simple-launcher

# stop-gap until there's real vala support in automake.
VALA_FILES =	\
	applet.vala	\
	$(NULL)
APPLET_CFLAGS =				\
	$(NULL)

include $(top_srcdir)/Makefile.vala-applet

include $(top_srcdir)/Makefile.schemas

applet_LTLIBRARIES = simple-launcher.la
simple_launcher_la_SOURCES =	\
	$(GENERATED_C_FILES)	\
	$(GENERATED_H_FILES)	\
	$(NULL)
simple_launcher_la_LIBADD =		\
	$(AWN_LIBS)			\
	$(SIMPLE_LAUNCHER_LIBS)	\
	$(NULL)
simple_launcher_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
