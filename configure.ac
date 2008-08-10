SAC_PREREQ(2.53)

m4_define(affinity_beagle_min_version,   0.0.12)
m4_define(affinity_tracker_min_version,  0.0.1)
m4_define(pycairo_required_version,      1.0.2) dnl or 1.1.7
m4_define(pygtk_required_version,        2.10.0)


AC_INIT(awn-extras-applets, 0.3.1, [])
AM_INIT_AUTOMAKE()
AC_CONFIG_SRCDIR(src)
AM_CONFIG_HEADER(config.h)
AM_MAINTAINER_MODE

AC_ISC_POSIX
AC_PROG_CC
AC_STDC_HEADERS
AC_PROG_LIBTOOL

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

PKG_CHECK_EXISTS([libwnck-1.0 >= 2.21.99.9], [AC_DEFINE(HAVE_LIBWNCK_222, 1, [Have libwnck 2.22.x])])

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

AC_ARG_WITH([gconf], AS_HELP_STRING([--without-gconf],[Disable building/installing applets that need GConf]),,[with_gconf=yes])
AC_ARG_WITH([gnome], AS_HELP_STRING([--without-gnome],[Disable building/installing applets that require Gnome-specific libraries]),,[with_gnome=yes])
AC_ARG_WITH([webkit], AS_HELP_STRING([--with-webkit],[Enable building/installing applets that require webkitgtk]),,[with_webkit=no])
AM_CONDITIONAL(WITH_GCONF, test "$with_gconf" != "no")
AM_CONDITIONAL(WITH_GNOME, test "$with_gnome" != "no")
AM_CONDITIONAL(WITH_WEBKIT, test "$with_webkit" != "no")

# all
PKG_CHECK_MODULES(AWN, [awn >= 0.3.1])
#trash
PKG_CHECK_MODULES(LIBGLADE, [libglade-2.0])
# awn-notification-daemon, shiny-switcher, standalone-launcher, switcher, taskmand
PKG_CHECK_MODULES(LIBWNCK, [libwnck-1.0])
# affinity, awn-notification-daemon, shiny-switcher, trash
PKG_CHECK_MODULES(LIBX11, [x11])
PKG_CHECK_MODULES(COMPOSITE, [xcomposite])
PKG_CHECK_MODULES(XRENDER, [xrender])
# awn-notification-daemon, cairo-menu
PKG_CHECK_MODULES(LIBSEXY, [libsexy])
PKG_CHECK_MODULES(LIBNOTIFY, [libnotify])
# standalone-launcher, taskmand, taskmand-applet
PKG_CHECK_MODULES(DBUS_GLIB, [dbus-glib-1])
# awn-terminal
PKG_CHECK_MODULES(VTE, [vte])

if test "$with_gconf" != "no" -o "$with_gnome" != "no"; then
# filebrowser
PKG_CHECK_MODULES(GNOMEUI, [libgnomeui-2.0])
# filebrowser
PKG_CHECK_MODULES(GNOME_DESKTOP, [gnome-desktop-2.0])
# filebrowser, cairo-menu, trash, trasher
PKG_CHECK_MODULES(GNOME_VFS, [gnome-vfs-2.0])
# clock
PKG_CHECK_MODULES(RSVG, [librsvg-2.0])
# main-menu, cairo-menu
PKG_CHECK_MODULES(GNOME_MENU, [libgnome-menu])
# awn-system-monitor
PKG_CHECK_MODULES(GTOP, [libgtop-2.0])
fi

webkit_module=no
if test "$with_webkit" != "no"; then
# webapplet
PKG_CHECK_EXISTS([webkit-1.0],[webkit_module="webkit-1.0"],
    [PKG_CHECK_EXISTS([WebKitGtk],[
        webkit_module="WebKitGtk"
        AC_DEFINE([HAVE_OLD_WEBKITGTK],[1],[Define if the installed WebKit uses the old pkgconfig file and header structure.])
        ],[AC_MSG_ERROR([Could not find packages webkit-1.0 or WebKitGtk.  Either one is required for webkit support to be enabled.])])])
PKG_CHECK_MODULES(WEBKIT, [$webkit_module])
AC_SUBST(WEBKIT_CFLAGS)
AC_SUBST(WEBKIT_LIBS)
fi

#awn-notification-daemon
AC_ARG_ENABLE(sound,
    AS_HELP_STRING([--enable-sound=auto|gstreamer|no],[Sound support for awn-notification-daemon (default=auto)])
)

if test x$enable_sound != xno -a x$enable_sound != xgstreamer; then
	enable_sound=auto
fi

if test x$enable_sound != xno; then
	gstreampkg="gstreamer-0.10"

	if test x$enable_sound = xauto; then
		PKG_CHECK_MODULES(GSTREAMER, $gstreampkg,
		                  [enable_sound=gstreamer], [enable_sound=no])
	else
		PKG_CHECK_MODULES(GSTREAMER, $gstreampkg, [enable_sound=gstreamer])
	fi

	if test x$enable_sound = xgstreamer; then
		AC_DEFINE([HAVE_GSTREAMER], 1, [Defined if Gstreamer is detected])
    else
        gstreampkg=
	fi
fi


# affinity
affinity_pkgs="x11"
affinity_beagle_pkg="libbeagle-0.0 >= affinity_beagle_min_version"
AC_MSG_CHECKING([for optional Beagle support (Affinity)])
PKG_CHECK_EXISTS([$affinity_beagle_pkg], [
    AC_DEFINE(HAVE_BEAGLE, 1, [Define to enable beagle support])
    have_beagle=yes
    affinity_pkgs="$affinity_pkgs $affinity_beagle_pkg"
], [have_beagle=no])
AC_MSG_RESULT([$have_beagle])
AM_CONDITIONAL(HAVE_BEAGLE, test "$have_beagle" = "yes")

affinity_tracker_pkg="tracker >= affinity_tracker_min_version"
AC_MSG_CHECKING([for optional Tracker support (Affinity)])
PKG_CHECK_EXISTS([$affinity_tracker_pkg], [
    AC_DEFINE(HAVE_TRACKER, 1, [Define to enable tracker support])
    have_tracker=yes
    affinity_pkgs="$affinity_pkgs $affinity_tracker_pkg"
], [have_tracker=no])
AC_MSG_RESULT([$have_tracker])
AM_CONDITIONAL(HAVE_TRACKER, test "$have_tracker" = "yes")

# applet-specific libraries
PKG_CHECK_MODULES(AFFINITY, [$affinity_pkgs])
if test "$with_gconf" != "no" -o "$with_gnome" != "no"; then
PKG_CHECK_MODULES(FILEBROWSER, [gnome-desktop-2.0 gnome-vfs-2.0 libgnomeui-2.0])
PKG_CHECK_MODULES(CAIRO_MENU_GNOME, [gnome-vfs-2.0 libgnome-menu libnotify libsexy])
PKG_CHECK_MODULES(TRASH, [gnome-vfs-2.0 libglade-2.0 x11])
fi
PKG_CHECK_MODULES(NOTIFICATION_DAEMON, [$gstreampkg libnotify libsexy libwnck-1.0 x11])
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
    # volume-control
    AM_CHECK_PYMOD(alsaaudio,,,AC_MSG_ERROR([python module alsaaudio required (python-alsaaudio)]))
    # arss, mail
    AM_CHECK_PYMOD(feedparser,,,AC_MSG_ERROR([python module feedparser required (python-feedparser)]))
    if test "$with_gnome" != "no"; then
    # MiMenu
    AM_CHECK_PYMOD(gmenu,,,AC_MSG_ERROR([python module gmenu required]))
    fi
    if test "$with_gconf" != "no" -o "$with_gnome" != "no"; then
    # stacks
    AM_CHECK_PYMOD(gnomedesktop,,,AC_MSG_ERROR([python module gnomedesktop required]))
    # calendar, stacks
    AM_CHECK_PYMOD(gnomevfs,,,AC_MSG_ERROR([python module gnomevfs required]))
    # stacks
    AM_CHECK_PYMOD(gnome.ui,,,AC_MSG_ERROR([python module gnome.ui required]))
    # awn-meebo, digg, pandora
    AM_CHECK_PYMOD(gtkmozembed,,,AC_MSG_ERROR([python module gtkmozembed required]))
    fi
    if test "$with_gconf" != "no"; then
    # lastfm
    AM_CHECK_PYMOD(gst,,,AC_MSG_ERROR([python module gstreamer required (python-gst0.10)]))
    fi
fi

dnl
dnl Check if desktop-agnostic is installed.
dnl

AWN_BINDIR=`$PKG_CONFIG --variable=exec_prefix awn`/bin
AC_SUBST(AWN_BINDIR)

config_backend=`$PKG_CONFIG --variable=config_backend awn`
dnl
dnl Check for Vala support.
dnl
AWN_VAPIDIR=`$PKG_CONFIG --variable=vapidir awn`
if test -n "$AWN_VAPIDIR" -a -f "$AWN_VAPIDIR/awn.vapi"; then
    VALA_PROG_VALAC(0.3.4)
    AC_PATH_PROG(VAPIGEN, vapigen, vapigen, [])
    AC_SUBST(AWN_VAPIDIR)
fi
AM_CONDITIONAL(GCONF_SCHEMAS, test "$config_backend" = "GConf")
AM_CONDITIONAL(HAVE_VALA, test -n "$AWN_VAPIDIR" -a -n "$VALAC")
AM_CONDITIONAL(LIBAWN_USE_GNOME, test -n "`echo $AWN_CFLAGS | grep LIBAWN_USE_GNOME`")

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

DBUS_SERVICES_DIR=`$PKG_CONFIG --variable=session_bus_services_dir dbus-1`
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
if test "$config_backend" = "GConf" -o "$with_gconf" != "no"; then
AC_PATH_PROG(GCONFTOOL, gconftool-2, no)
  if test x"$GCONFTOOL" = xno; then
    AC_MSG_ERROR([gconftool-2 executable not found in your path - should be installed with GConf])
  fi
fi

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
src/arss/icons/Makefile
src/awn-meebo/Makefile
src/awn-meebo/awn-meebo.desktop.in
src/awn-meebo/icons/Makefile
src/awn-meebo/profile/Makefile
src/awn-notification-daemon/Makefile
src/awn-notification-daemon/data/Makefile
src/awn-notification-daemon/po/Makefile.in
src/awn-notification-daemon/src/Makefile
src/awn-notification-daemon/src/daemon/Makefile
src/awn-notification-daemon/src/daemon/awnnotificationdaemon.desktop.in
src/awnsystemmonitor/Makefile
src/awnsystemmonitor/awnsystemmonitor.desktop.in
src/awnterm/Makefile
src/awnterm/awnterm.desktop.in
src/battery-applet/battery-applet.desktop.in
src/battery-applet/Makefile
src/battery-applet/icons/Makefile
src/clock/Makefile
src/clock/clock.desktop.in
src/cairo-clock/Makefile
src/cairo-clock/cairo-clock.desktop.in
src/cairo-clock/themes/Makefile
src/cairo-clock/themes/gnome/Makefile
src/cairo-clock/themes/onox/Makefile
src/cairo-clock/themes/tango/Makefile
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
src/calendar/icalendar/Makefile
src/calendar/dateutil/Makefile
src/calendar/dateutil/zoneinfo/Makefile
src/comic/Makefile
src/comic/comic.desktop.in
src/comic/icons/Makefile
src/comics/comics.desktop.in
src/comics/Makefile
src/comics/feeds/Makefile
src/comics/glade/Makefile
src/comics/locale/Makefile
src/comics/icons/Makefile
src/comics/locale/sv_SE/Makefile
src/comics/locale/sv_SE/LC_MESSAGES/Makefile
src/digg/digg.desktop.in
src/digg/Makefile
src/digg/icons/Makefile
src/digg/profile/Makefile
src/digg/profile/Cache/Makefile
src/digitalClock/Makefile
src/digitalClock/digitalClock.desktop.in
src/file-browser-launcher/Makefile
src/file-browser-launcher/icons/Makefile
src/file-browser-launcher/file-browser-launcher.desktop.in
src/filebrowser/Makefile
src/filebrowser/filebrowser.desktop.in
src/lastfm/Makefile
src/lastfm/icons/Makefile
src/lastfm/lastfm.desktop.in
src/libawn-extras/Makefile
src/libawn-extras/awn-extras.pc
src/libawn-extras/bindings/Makefile
src/libawn-extras/bindings/python/Makefile
src/libawn-extras/bindings/vala/Makefile
src/mail/Makefile
src/mail/Themes/Makefile
src/mail/Themes/Tango/Makefile
src/mail/Themes/Reserved/Makefile
src/mail/Themes/GMail/Makefile
src/mail/mail.desktop.in
src/mail/locale/Makefile
src/mail/locale/ru/Makefile
src/mail/locale/ru/LC_MESSAGES/Makefile
src/main-menu/Makefile
src/main-menu/main-menu.desktop.in
src/media-control/Makefile
src/media-control/icons/Makefile
src/media-control/media-control.desktop.in
src/media-icon-back/Makefile
src/media-icon-back/icons/Makefile
src/media-icon-back/media-icon-back.desktop.in
src/media-icon-next/Makefile
src/media-icon-next/icons/Makefile
src/media-icon-next/media-icon-next.desktop.in
src/media-icon-play/Makefile
src/media-icon-play/icons/Makefile
src/media-icon-play/media-icon-play.desktop.in
src/media-player/Makefile
src/media-player/icons/Makefile
src/media-player/media-player.desktop.in
src/mount-applet/Makefile
src/mount-applet/icons/Makefile
src/mount-applet/mount-applet.desktop.in
src/MiMenu/Makefile
src/MiMenu/icons/Makefile
src/MiMenu/mimenu.desktop.in
src/notification-area/Makefile
src/notification-area/notification-area.desktop.in
src/pandora/Makefile
src/pandora/icons/Makefile
src/pandora/pandora.desktop.in
src/places/Makefile
src/places/places.desktop.in
src/plugger/Makefile
src/plugger/plugger.desktop.in
src/pynot/Makefile
src/pynot/pynot.desktop.in
src/python-test/Makefile
src/python-test/python-test.desktop.in
src/quit-applet/Makefile
src/quit-applet/icons/Makefile
src/quit-applet/quit-applet.desktop.in
src/rtm/Makefile
src/rtm/rtm.desktop.in
src/rtm/icons/Makefile
src/separator/Makefile
src/separator/separator.desktop.in
src/shiny-switcher/Makefile
src/shiny-switcher/shinyswitcher.desktop.in
src/simple-launcher/Makefile
src/simple-launcher/simple-launcher.desktop.in
src/showdesktop/Makefile
src/showdesktop/showdesktop.desktop.in
src/stacks/Makefile
src/stacks/icons/Makefile
src/stacks/stacks.desktop.in
src/standalone-launcher/Makefile
src/standalone-launcher/standalone-launcher.desktop.in
src/switcher/Makefile
src/switcher/switcher.desktop.in
src/taskmand/Makefile
src/taskmand/data/Makefile
src/Taskmand-applet/Makefile
src/Taskmand-applet/Taskmand-applet.desktop.in
src/thinkhdaps/Makefile
src/thinkhdaps/images/Makefile
src/thinkhdaps/thinkhdaps.desktop.in
src/to-do/Makefile
src/to-do/to-do.desktop.in
src/tomboy-applet/Makefile
src/tomboy-applet/icons/Makefile
src/tomboy-applet/tomboy-applet.desktop.in
src/trash/Makefile
src/trash/trash.desktop.in
src/trasher/Makefile
src/trasher/trasher.desktop.in
src/tsclient-applet/Makefile
src/tsclient-applet/icons/Makefile
src/tsclient-applet/tsclient-app.desktop.in
src/vala-test/Makefile
src/vala-test/vala-test.desktop.in
src/volume-control/Makefile
src/volume-control/themes/Makefile
src/volume-control/themes/Black/Makefile
src/volume-control/themes/Minimal/Makefile
src/volume-control/volume-control.desktop.in
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
src/weather/weather.desktop.in
src/webapplet/Makefile
src/webapplet/webapplet.desktop.in
src/wobblyzini/Makefile
src/wobblyzini/wobblyzini.desktop.in
src/wobblyzini/icons/Makefile
])

dnl ========================================================================

echo ""
echo "         Avant Window Navigator Extras $VERSION"
echo "         ==================================="
echo ""
echo "                   prefix:   ${prefix}"
echo ""
echo "    Configuration Backend:   $config_backend"
echo ""
echo "             Vala Support:   $HAVE_VALA"
echo ""
echo "           WebKit Support:   $webkit_module"
echo ""
