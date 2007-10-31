schemasdir       = $(GCONF_SCHEMA_FILE_DIR)
schemas_in_files = notification-daemon.schemas.in
schemas_DATA     = $(schemas_in_files:.schemas.in=.schemas)

@INTLTOOL_SCHEMAS_RULE@

if GCONF_SCHEMAS_INSTALL
install-data-local:
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(schemas_DATA)
else
install-data-local:
endif

EXTRA_DIST = \
	$(schemas_in_files) 

CLEANFILES = $(schemas_DATA)
