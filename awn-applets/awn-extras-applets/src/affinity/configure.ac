AC_PREREQ(2.53)

m4_define(beagle_minver,               0.0.12)
m4_define(tracker_minver,              0.0.1)

AC_INIT(affinity, 0.1, [http://code.google.com/p/affinity-search/])
AM_INIT_AUTOMAKE()
AC_CONFIG_SRCDIR(src/main.c)
AM_CONFIG_HEADER(config.h)
AM_MAINTAINER_MODE

AC_ISC_POSIX
AC_PROG_CC
AC_STDC_HEADERS

PKG_CHECK_MODULES(DEPS, gnome-vfs-2.0 gtk+-2.0 libgnome-2.0 gnome-vfs-2.0 gconf-2.0 x11 xproto gnome-desktop-2.0 awn)
AC_SUBST(DEPS_CFLAGS)
AC_SUBST(DEPS_LIBS)

if test "x$GCC" = "xyes"; then
        GCC_FLAGS="-g -Wall"
fi

AC_SUBST(GCC_FLAGS)

dnl ==========================================================================
dnl i18n
dnl ==========================================================================

GETTEXT_PACKAGE=affinity
AC_SUBST(GETTEXT_PACKAGE)
AC_SUBST([CONFIG_STATUS_DEPENDENCIES],['$(top_srcdir)/po/LINGUAS'])
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE", [Define to the Gettext package name])
ALL_LINGUAS="`cat "$srcdir/po/LINGUAS" | grep -v '^#'`"

IT_PROG_INTLTOOL([0.34])

AM_GLIB_GNU_GETTEXT

dnl ==========================================================================
dnl applet
dnl ==========================================================================

AM_CONDITIONAL(HAVE_APPLET, false)

dnl libpanelapplet checking
			    			  
AC_ARG_ENABLE(applet, [  --disable-applet     build without the gnome panel applet])
msg_applet=no
if test "x$enable_applet" != "xno"; then
	PKG_CHECK_MODULES(APPLET, libpanelapplet-2.0, [
		  	  AM_CONDITIONAL(HAVE_APPLET, true)
			  AC_DEFINE(HAVE_APPLET, 1, [Define to enable applet support])
			  ]
                          msg_applet=yes,
	          	  [AM_CONDITIONAL(HAVE_APPLET, false)])
        AC_SUBST(APPLET_CFLAGS)
	AC_SUBST(APPLET_LIBS)
fi

dnl ==========================================================================
dnl search implementations
dnl ==========================================================================

AM_CONDITIONAL(HAVE_TRACKER, false)

dnl libtracker checking
			    			  
AC_ARG_ENABLE(tracker, [  --disable-tracker     build without tracker support])
msg_tracker=no
if test "x$enable_tracker" != "xno"; then
	PKG_CHECK_MODULES(TRACKER, tracker >= tracker_minver, [
		  	  AM_CONDITIONAL(HAVE_TRACKER, true)
			  AC_DEFINE(HAVE_TRACKER, 1, [Define to enable tracker support])
			  ]
                          msg_tracker=yes,
	          	  [AM_CONDITIONAL(HAVE_TRACKER, false)])
        AC_SUBST(TRACKER_CFLAGS)
	AC_SUBST(TRACKER_LIBS)
fi

dnl ==========================================================================


AM_CONDITIONAL(HAVE_BEAGLE, false)

dnl libbeagle checking
			    			  
AC_ARG_ENABLE(beagle, [  --disable-beagle     build without beagle support])
msg_beagle=no
if test "x$enable_beagle" != "xno"; then
	PKG_CHECK_MODULES(BEAGLE, libbeagle-0.0 >= beagle_minver, [
		  	  AM_CONDITIONAL(HAVE_BEAGLE, true)
			  AC_DEFINE(HAVE_BEAGLE, 1, [Define to enable beagle support])
			  ]
                          msg_beagle=yes,
	          	  [AM_CONDITIONAL(HAVE_BEAGLE, false)])
        AC_SUBST(BEAGLE_CFLAGS)
	AC_SUBST(BEAGLE_LIBS)
fi

dnl ==========================================================================

AC_OUTPUT([
Makefile
affinity-preferences/Makefile
data/Makefile
data/16x16/Makefile
data/22x22/Makefile
data/24x24/Makefile
data/48x48/Makefile
data/scalable/Makefile
data/actions/Makefile
src/Makefile
po/Makefile.in
])

dnl ==========================================================================
echo "
affinity-$VERSION:

	prefix:                 ${prefix}
	source code location:	${srcdir}
	compiler:		${CC}
	applet support		$msg_applet
	tracker support:	$msg_tracker
	beagle support:		$msg_beagle
"
