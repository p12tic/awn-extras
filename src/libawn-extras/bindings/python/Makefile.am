NULL =

# awn python scripts
pyawn_extrasdir = $(PYTHON_SITE_PKG)/awn/extras
pyawn_extras_PYTHON =	\
	__init__.py	\
	awnlib.py	\
	awnmediaplayers.py	\
	defs.py	\
	detach.py

AM_CFLAGS = \
	$(PYTHON_CPPFLAGS) \
	$(PYGTK_CFLAGS) \
	$(PYCAIRO_CFLAGS) \
	$(AWN_CFLAGS) \
	-I$(top_builddir)/src \
	-DHAVE_PYCAIRO \
	$(NULL)

# libawn-extras python extensions
pyawn_extrasexecdir = $(PYTHON_SITE_PKG)/awn/extras
pyawn_extrasexec_LTLIBRARIES = _extras.la

common_ldflags = -module -avoid-version

AWN_EXTRAS_DEFS = awn_extras.defs
AWN_EXTRAS_OVERRIDE = awn_extras.override
CLEANFILES = awn_extras.c
EXTRA_DIST = $(AWN_EXTRAS_DEFS) $(AWN_EXTRAS_OVERRIDE)
awn_extras.c: $(AWN_EXTRAS_DEFS) $(AWN_EXTRAS_OVERRIDE)

_extras_la_LDFLAGS = $(common_ldflags) -export-symbols-regex init_extras

_extras_la_LIBADD = \
	$(PYTHON_LDFLAGS) \
	$(PYTHON_EXTRA_LIBS) \
	$(PYTHON_EXTRA_LDFLAGS) \
	$(PYGTK_LIBS) \
	$(PYCAIRO_LIBS) \
	$(AWN_LIBS) \
	$(top_builddir)/src/libawn-extras/libawn-extras.la \
	$(NULL)

_extras_la_SOURCES = awn_extrasmodule.c
nodist__extras_la_SOURCES = awn_extras.c

defsdir = $(datarootdir)/avant-window-navigator/defs
defs_DATA = $(AWN_EXTRAS_DEFS)

# code generator
.defs.c:
	@echo "***INFO*** Generating $*.c from $*.defs" \
	&& ( $(PYGTK_CODEGEN) \
	    -I $(srcdir) \
	    --py_ssize_t-clean \
	    --register $(PYGTK_DEFSDIR)/gdk-types.defs \
	--override $(srcdir)/$*.override \
	    --prefix py$* $<) > gen-$*.c \
	&& cp -f gen-$*.c $*.c \
	&& rm -f gen-$*.c

