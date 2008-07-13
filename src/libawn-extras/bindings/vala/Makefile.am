# adapted from vala's vapi/Makefile.am
NULL =

vapidir = $(datadir)/vala/vapi

dist_vapi_DATA =	\
	awn-extras.vapi	\
	awn-extras.deps	\
	$(NULL)

dist_noinst_DATA =		\
	awn-extras.files	\
	awn-extras.gi		\
	awn-extras.metadata	\
	awn-extras.namespace	\
	$(NULL)

awn-extras.vapi: awn-extras.gi awn-extras.metadata
	$(VAPIGEN) --vapidir=$(AWN_VAPIDIR) --library=awn-extras $<
