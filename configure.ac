SAC_PREREQ(2.53)

AFFINITY_BEAGLE_MIN_VERSION="0.0.12"
AFFINITY_TRACKER_MIN_VERSION="0.0.1"
m4_define(pycairo_required_version,      1.0.2) dnl or 1.1.7
m4_define(pygtk_required_version,        2.10.0)


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

dnl
dnl Python bindings support
dnl

AC_PYTHON_DEVEL()

PKG_CHECK_MODULES(PYCAIRO, pycairo >= pycairo_required_version)
PYGTK_CODEGEN_DEFINES="-DHAVE_PYCAIRO $PYGTK_CODEGEN_DEFINES";

PKG_CHECK_MODULES(PYGTK, pygtk-2.0 >= pygtk_required_version)
AC_PATH_PROG(PYGTK_CODEGEN, pygtk-codegen-2.0, no)
if test "x$PYGTK_CODEGEN" = "xno"; then
  AC_MSG_ERROR([could not find pygtk-codegen-2.0 script])
fi

AC_MSG_CHECKING(for pygtk defs)
PYGTK_DEFSDIR=`$PKG_CONFIG --variable=defsdir pygtk-2.0`
AC_SUBST(PYGTK_DEFSDIR)
AC_MSG_RESULT($PYGTK_DEFSDIR)

dnl
dnl library support
dnl

AC_CHECK_LIB(m, round)

dnl
dnl package support
dnl

# all
PKG_CHECK_MODULES(AWN, [awn])
# filebrowser
PKG_CHECK_MODULES(GNOMEUI, [libgnomeui-2.0])
# filebrowser, affinity
PKG_CHECK_MODULES(GNOME_DESKTOP, [gnome-desktop-2.0])
# filebrowser, cairo-menu
PKG_CHECK_MODULES(GNOME_VFS, [gnome-vfs-2.0])
#trash
PKG_CHECK_MODULES(LIBGLADE, [libglade-2.0])
# awn-notification-daemon, shiny-switcher, standalone-launcher, switcher, taskmand
PKG_CHECK_MODULES(LIBWNCK, [libwnck-1.0])
# affinity, shiny-switcher
PKG_CHECK_MODULES(LIBX11, [x11])
PKG_CHECK_MODULES(COMPOSITE, [xcomposite])
PKG_CHECK_MODULES(XRENDER, [xrender])
# clock
PKG_CHECK_MODULES(RSVG, [librsvg-2.0])
# main-menu, cairo-menu
PKG_CHECK_MODULES(GNOME_MENU, [libgnome-menu])
# awn-system-monitor
PKG_CHECK_MODULES(GTOP, [libgtop-2.0])
# awn-notification-daemon, cairo-menu
PKG_CHECK_MODULES(LIBSEXY, [libsexy])
PKG_CHECK_MODULES(LIBNOTIFY, [libnotify])
# awn-terminal
PKG_CHECK_MODULES(VTE, [vte])
# standalone-launcher, taskmand, taskmand-applet
PKG_CHECK_MODULES(DBUS_GLIB, [dbus-glib-1])

# affinity
affinity_pkgs="gnome-desktop-2.0 gnome-vfs-2.0 x11"
affinity_beagle_pkg="libbeagle-0.0 >= $AFFINITY_BEAGLE_MIN_VERSION"
PKG_CHECK_MODULES(BEAGLE, [$affinity_beagle_pkg], [
    AC_DEFINE(HAVE_BEAGLE, 1, [Define to enable beagle support])
    have_beagle=yes
    affinity_pkgs="$affinity_pkgs $affinity_beagle_pkg"
], [have_beagle=no])
AM_CONDITIONAL(HAVE_BEAGLE, test "$have_beagle" = "yes")

affinity_tracker_pkg="tracker >= $AFFINITY_TRACKER_MIN_VERSION"
PKG_CHECK_MODULES(TRACKER, [$affinity_tracker_pkg], [
    AC_DEFINE(HAVE_TRACKER, 1, [Define to enable tracker support])
    have_tracker=yes
    affinity_pkgs="$affinity_pkgs $affinity_tracker_pkg"
], [have_tracker=no])
AM_CONDITIONAL(HAVE_TRACKER, test "$have_tracker" = "yes")

# applet-specific libraries
PKG_CHECK_MODULES(AFFINITY, [$affinity_pkgs])
PKG_CHECK_MODULES(FILEBROWSER, [gnome-desktop-2.0 gnome-vfs-2.0 libgnomeui-2.0])
PKG_CHECK_MODULES(CAIRO_MENU_GNOME, [gnome-vfs-2.0 libgnome-menu libnotify libsexy])
PKG_CHECK_MODULES(NOTIFICATION_DAEMON, [libnotify libsexy libwnck-1.0])
PKG_CHECK_MODULES(SHINY_SWITCHER, [libwnck-1.0 x11 xcomposite xrender])
PKG_CHECK_MODULES(STANDALONE_LAUNCHER, [dbus-glib-1 libwnck-1.0])
PKG_CHECK_MODULES(TASKMAND, [dbus-glib-1 libwnck-1.0])
PKG_CHECK_MODULES(TASKMAND_APPLET, [dbus-glib-1])

dnl
dnl Check python modules
dnl
AC_ARG_ENABLE(pymod_checks, 
              AC_HELP_STRING([--disable-pymod-checks], [Disable checks for Python modules]),
              enable_pymod_checks=$enableval,
	      enable_pymod_checks=yes)
              
if test x${enable_pymod_checks} = xyes; then
  AM_CHECK_PYMOD(alsaaudio,,,AC_MSG_ERROR([python module alsaaudio required (python-alsaaudio)]))
  AM_CHECK_PYMOD(libgmail,,,AC_MSG_ERROR([python module libgmail required (python-libgmail)]))
  AM_CHECK_PYMOD(gst,,,AC_MSG_ERROR([python module gstreamer required (python-gst0.10)]))
fi

dnl
dnl Check if desktop-agnostic is installed.
dnl

AC_CHECK_LIB([awn], [awn_vfs_init], [have_desktop_agnostic=yes], [have_desktop_agnostic=no], [$AWN_LIBS])
if test "$have_desktop_agnostic" = "yes"; then
    config_backend=`$PKG_CONFIG --variable=config_backend awn`
    AC_DEFINE(USE_AWN_DESKTOP_AGNOSTIC, 1, [Use the APIs that originated in the desktop-agnostic branch of Awn.])
    dnl
    dnl Check for Vala support.
    dnl
    AWN_VAPIDIR=`$PKG_CONFIG --variable=vapidir awn`
    if test -n "$AWN_VAPIDIR"; then
        VALA_PROG_VALAC(0.1.6)
        AC_SUBST(AWN_VAPIDIR)
    fi
fi
AM_CONDITIONAL(DESKTOP_AGNOSTIC, test "$have_desktop_agnostic" = "yes")
AM_CONDITIONAL(GCONF_SCHEMAS, test "$have_desktop_agnostic" = "no" -o "$config_backend" = "GConf")
AM_CONDITIONAL(HAVE_VALA, test -n "$AWN_VAPIDIR" -a -n "$VALAC")

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


AS_AC_EXPAND(ICONDIR, $icondir)
AS_AC_EXPAND(SYSCONFDIR, $sysconfdir)
AS_AC_EXPAND(LIBDIR, $libdir)
AS_AC_EXPAND(DATADIR, $datadir)
AS_AC_EXPAND(LIBEXECDIR, $libexecdir)

DBUS_SERVICES_DIR="/usr/share/dbus-1/services"
AC_SUBST(DBUS_SERVICES_DIR)


icondir="$datarootdir/avant-window-navigator/applets/icons"
AC_SUBST(icondir)

if test "x$GCC" = "xyes"; then
        GCC_FLAGS="-g -Wall"
fi

AC_SUBST(GCC_FLAGS)

dnl ==============================================
dnl GConf
dnl ==============================================
AM_GCONF_SOURCE_2

dnl Please keep in alphabetical order
AC_OUTPUT([
Makefile
po/Makefile.in
src/Makefile
src/affinity/Makefile
src/affinity/affinity.desktop.in
src/affinity/affinity-preferences/Makefile
src/affinity/affinity-preferences/affinity-preferences
src/affinity/data/Makefile
src/affinity/data/16x16/Makefile
src/affinity/data/22x22/Makefile
src/affinity/data/24x24/Makefile
src/affinity/data/48x48/Makefile
src/affinity/data/scalable/Makefile
src/affinity/data/actions/Makefile
src/affinity/po/Makefile.in
src/arss/Makefile
src/arss/arss.desktop.in
src/arss/Core/Makefile
src/awn-meebo/Makefile
src/awn-meebo/awn-meebo.desktop.in
src/awn-meebo/profile/Makefile
src/awn-notification-daemon/Makefile
src/awn-notification-daemon/data/Makefile
src/awn-notification-daemon/po/Makefile.in
src/awn-notification-daemon/src/Makefile
src/awn-notification-daemon/src/daemon/Makefile
src/awn-notification-daemon/src/daemon/awnnotificationdaemon.desktop.in
src/awnsystemmonitor/Makefile
src/awnterm/Makefile
src/battery-applet/Makefile
src/battery-applet/icons/Makefile
src/battery-applet/battery-applet.desktop.in
src/BlingSwitcher/Makefile
src/BlingSwitcher/BlingSwitcher.desktop.in
src/clock/Makefile
src/cairo-menu-classic/Makefile
src/cairo-menu-classic/cairo_main_menu_classic.desktop.in
src/cairo-menu/Makefile
src/cairo-menu/cairo_main_menu.desktop.in
src/calendar/Makefile
src/calendar/calendar.desktop.in
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
src/comic/comic.desktop.in
src/comic/images/Makefile
src/digg/Makefile
src/digg/digg.desktop.in
src/digg/profile/Makefile
src/digg/profile/Cache/Makefile
src/digitalClock/Makefile
src/file-browser-launcher/Makefile
src/filebrowser/Makefile
src/gmail/Makefile
src/gmail/Themes/Makefile
src/gmail/Themes/Tango/Makefile
src/gmail/Themes/Reserved/Makefile
src/lastfm/Makefile
src/lastfm/icons/Makefile
src/libawn-extras/Makefile
src/libawn-extras/bindings/Makefile
src/libawn-extras/bindings/python/Makefile
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
src/notification-area/Makefile
src/notification-area/notification-area.desktop.in
src/showdesktop/Makefile
src/pandora/Makefile
src/places/Makefile
src/places/places.desktop.in
src/plugger/Makefile
src/PyClock/Makefile
src/PyClock/Themes/Makefile
src/PyClock/Themes/Plain-Clock/Makefile
src/PyClock/Themes/SBB/Makefile
src/PyClock/Themes/Tango/Makefile
src/python-test/Makefile
src/python-test/python-test.desktop.in
src/quit-applet/Makefile
src/quit-applet/icons/Makefile
src/volume-control/Makefile
src/separator/Makefile
src/shiny-switcher/Makefile
src/shiny-switcher/shinyswitcher.desktop.in
src/stacks/Makefile
src/stacks/icons/Makefile
src/standalone-launcher/Makefile
src/standalone-launcher/standalone-launcher.desktop.in
src/switcher/Makefile
src/taskmand/Makefile
src/taskmand/data/Makefile
src/Taskmand-applet/Makefile
src/Taskmand-applet/Taskmand-applet.desktop.in
src/trash/Makefile
src/trasher/Makefile
src/tsclient-applet/Makefile
src/tsclient-applet/icons/Makefile
src/vala-test/Makefile
src/vala-test/vala-test.desktop.in
src/volume-control/Themes/Makefile
src/volume-control/Themes/Black/Makefile
src/volume-control/Themes/Tango/Makefile
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
src/wobblyzini/wobblyzini.desktop.in
src/wobblyzini/icons/Makefile
])
