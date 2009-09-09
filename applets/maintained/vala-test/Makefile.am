APPLET_NAME = vala-test
VALA_FILES = \
	applet.vala \
	$(NULL)
include $(top_srcdir)/Makefile.vala-applet

applet_LTLIBRARIES = vala-test.la
vala_test_la_SOURCES = \
	$(VALA_C_FILES) \
	$(NULL)
vala_test_la_LIBADD = \
	$(AWN_LIBS) \
	$(NULL)
vala_test_la_LDFLAGS = $(APPLET_LINKER_FLAGS)
