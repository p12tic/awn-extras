APPLET_NAME = vala-test
# stop-gap until there's real vala support in automake.
VALA_FILES =	\
	applet.vala	\
	$(NULL)
include $(top_srcdir)/Makefile.vala-applet

applet_LTLIBRARIES = vala-test.la
vala_test_la_SOURCES =		\
	$(GENERATED_C_FILES)	\
	$(GENERATED_H_FILES)	\
	$(NULL)
vala_test_la_LIBADD =	\
	$(AWN_LIBS)			\
	$(NULL)
vala_test_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
