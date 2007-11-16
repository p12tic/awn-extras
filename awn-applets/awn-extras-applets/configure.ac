AC_PREREQ(2.53)
AC_INIT(awn-extras-applets, 0.2.1, [])
AM_INIT_AUTOMAKE()
AC_CONFIG_SRCDIR(src)
AM_CONFIG_HEADER(config.h)
AM_MAINTAINER_MODE

AC_ISC_POSIX
AC_PROG_CC
AC_STDC_HEADERS
AC_PROG_LIBTOOL

dnl ==============================================
dnl gconf stuff
dnl ==============================================
AC_PATH_PROG(GCONFTOOL, gconftool-2, no)
if test x"$GCONFTOOL" = xno; then
  AC_MSG_ERROR([gconftool-2 executable not found in your path - should be installed with GConf])
fi

dnl ==============================================
dnl translation support
dnl ==============================================

GETTEXT_PACKAGE=awn-extras-applets
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE,"$GETTEXT_PACKAGE", [Gettext package])
ALL_LINGUAS=""

IT_PROG_INTLTOOL([0.34])
AM_GLIB_GNU_GETTEXT

slicelocaledir='${prefix}/${DATADIRNAME}/locale'
AC_SUBST(slicelocaledir)

PKG_CHECK_MODULES(DEPS, 
                  gtk+-2.0
                  awn
                  libwnck-1.0 
                  libglade-2.0
                  libgnome-menu 
                  gnome-desktop-2.0
                  librsvg-2.0
                  libgtop-2.0
                  glib-2.0
	          dbus-1
	          dbus-glib-1
                  libsexy
	          gconf-2.0
	          gdk-2.0
		  gdk-pixbuf-2.0
		  libnotify)
AC_SUBST(DEPS_CFLAGS)
AC_SUBST(DEPS_LIBS)
AC_SUBST(GDK_CFLAGS)
AC_SUBST(GDK_LIBS)

dnl
dnl Check the D-BUS version.
dnl

AC_MSG_CHECKING([dbus version])
DBUS_VERSION=`$PKG_CONFIG --modversion dbus-1`
DBUS_MAJOR_VER=`echo $DBUS_VERSION | cut -d. -f 1`
DBUS_MINOR_VER=`echo $DBUS_VERSION | cut -d. -f 2`
DBUS_MICRO_VER=`echo $DBUS_VERSION | cut -d. -f 3`

AC_MSG_RESULT($DBUS_VERSION)
AC_DEFINE_UNQUOTED(DBUS_MAJOR_VER, $DBUS_MAJOR_VER, [D-BUS major version.])
AC_DEFINE_UNQUOTED(DBUS_MINOR_VER, $DBUS_MINOR_VER, [D-BUS minor version.])
AC_DEFINE_UNQUOTED(DBUS_MICRO_VER, $DBUS_MICRO_VER, [D-BUS micro version.])

AC_DEFINE_UNQUOTED(DBUS_API_SUBJECT_TO_CHANGE, ,DBUS API is subject to change)

AS_AC_EXPAND(SYSCONFDIR, $sysconfdir)
AS_AC_EXPAND(LIBDIR, $libdir)
AS_AC_EXPAND(DATADIR, $datadir)
AS_AC_EXPAND(LIBEXECDIR, $libexecdir)

if test "x$GCC" = "xyes"; then
        GCC_FLAGS="-g -Wall"
fi

AC_SUBST(GCC_FLAGS)

dnl ==============================================
dnl GConf
dnl ==============================================
AM_GCONF_SOURCE_2

dnl Please keep in alpha order

dnl ==============================================
dnl GConf
dnl ==============================================
AM_GCONF_SOURCE_2
AC_OUTPUT([
Makefile
src/Makefile
src/awn-meebo/Makefile
src/awn-meebo/profile/Makefile
src/awn-notification-daemon/Makefile
src/awn-notification-daemon/data/Makefile
src/awn-notification-daemon/po/Makefile.in
src/awn-notification-daemon/src/Makefile
src/awn-notification-daemon/src/daemon/Makefile
src/awnsystemmonitor/Makefile
src/battery-applet/Makefile
src/battery-applet/icons/Makefile
src/BlingSwitcher/Makefile
src/cairo-menu/Makefile
src/calendar/Makefile
src/calendar/google/Makefile
src/calendar/google/atom/Makefile
src/calendar/google/gdata/Makefile
src/calendar/google/gdata/apps/Makefile
src/calendar/google/gdata/base/Makefile
src/calendar/google/gdata/calendar/Makefile
src/calendar/google/gdata/docs/Makefile
src/calendar/google/gdata/spreadsheet/Makefile
src/calendar/images/Makefile
src/comic/Makefile
src/comic/images/Makefile
src/digg/Makefile
src/digg/profile/Makefile
src/digg/profile/Cache/Makefile
src/digitalClock/Makefile
src/filebrowser/Makefile
src/gmail/Makefile
src/gmail/Themes/Makefile
src/gmail/Themes/Default/Makefile
src/lastfm/Makefile
src/lastfm/icons/Makefile
src/main-menu/Makefile
src/media-control/Makefile
src/media-control/icons/Makefile
src/media-icon-back/Makefile
src/media-icon-back/icons/Makefile
src/media-icon-next/Makefile
src/media-icon-next/icons/Makefile
src/media-icon-play/Makefile
src/media-icon-play/icons/Makefile
src/MiMenu/Makefile
src/MiMenu/icons/Makefile
src/showdesktop/Makefile
src/notification-area/Makefile
src/plugger/Makefile
src/PyClock/Makefile
src/PyClock/Themes/Makefile
src/PyClock/Themes/Plain-Clock/Makefile
src/PyClock/Themes/SBB/Makefile
src/PyClock/Themes/Tango/Makefile
src/python-test/Makefile
src/quit-applet/Makefile
src/quit-applet/icons/Makefile
src/separator/Makefile
src/volume-control/Makefile
src/volume-control/Themes/Makefile
src/volume-control/Themes/Black/Makefile
src/volume-control/Themes/Tango/Makefile
src/stacks/Makefile
src/stacks/icons/Makefile
src/switcher/Makefile
src/trash/Makefile
src/trasher/Makefile
src/tsclient-applet/Makefile
src/tsclient-applet/icons/Makefile
src/weather/Makefile
src/weather/images/Makefile
src/weather/locale/Makefile
src/weather/locale/es/Makefile
src/weather/locale/es/LC_MESSAGES/Makefile
src/weather/locale/fr/Makefile
src/weather/locale/fr/LC_MESSAGES/Makefile
src/weather/locale/nb/Makefile
src/weather/locale/nb/LC_MESSAGES/Makefile
src/weather/locale/nn/Makefile
src/weather/locale/nn/LC_MESSAGES/Makefile
src/weather/locale/pt/Makefile
src/weather/locale/pt/LC_MESSAGES/Makefile
src/wobblyzini/Makefile
src/wobblyzini/icons/Makefile
po/Makefile.in
])
