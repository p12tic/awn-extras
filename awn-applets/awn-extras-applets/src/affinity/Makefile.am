SUBDIRS = src data po affinity-preferences

#MAINTAINERCLEANFILES = aclocal.m4 compile config.guess config.sub configure depcomp install-sh ltmain.sh Makefile.in missing


EXTRA_DIST = 			\
	autogen.sh		\
	config.h.in		\
	intltool-merge.in	\
	intltool-update.in	\
	intltool-extract.in	



snapshot:
	$(MAKE) dist distdir=$(PACKAGE)-snap`date +"%Y%m%d"`
