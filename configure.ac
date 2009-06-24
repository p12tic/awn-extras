SAC_PREREQ(2.53)

m4_define(pycairo_required_version,      1.0.2) dnl or 1.1.7
m4_define(pygtk_required_version,        2.10.0)


AC_INIT(awn-extras-applets, 0.3.9, [])
AM_INIT_AUTOMAKE([-Wno-portability])
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
PKG_CHECK_MODULES(AWN, [awn >= 0.3.9])
#trash
PKG_CHECK_MODULES(LIBGLADE, [libglade-2.0])
# awn-notification-daemon, shiny-switcher, standalone-launcher, taskmand
PKG_CHECK_MODULES(LIBWNCK, [libwnck-1.0])
# awn-notification-daemon, shiny-switcher, trash
PKG_CHECK_MODULES(LIBX11, [x11])
PKG_CHECK_MODULES(COMPOSITE, [xcomposite])
PKG_CHECK_MODULES(XRENDER, [xrender])
# awn-notification-daemon, cairo-menu
PKG_CHECK_MODULES(LIBNOTIFY, [libnotify])
libsexy_required=no
url_label_module="gtk+-2.0 >= 2.17.1"
icon_entry_module="gtk+-2.0 >= 2.15.0"
# awn-notification-daemon (UrlLabel)
PKG_CHECK_EXISTS([$url_label_module],
                 [AC_DEFINE([HAVE_GTK_URL_LABEL], 1,
                            [Defined if GTK+ has support for hyperlinks in GtkLabels])],
                 [libsexy_required=yes;url_label_module="libsexy"])
# cairo-menu (IconEntry)
PKG_CHECK_EXISTS([$icon_entry_module],
                 [AC_DEFINE([HAVE_GTK_ICON_ENTRY], 1,
                            [Defined if GTK+ has support for icons in GtkEntrys])],
                 [libsexy_required=yes;icon_entry_module="libsexy"])
if test "$libsexy_required" != "no"; then
    PKG_CHECK_MODULES(LIBSEXY, [libsexy])
fi
# standalone-launcher, taskmand, taskmand-applet
PKG_CHECK_MODULES(DBUS_GLIB, [dbus-glib-1])
# awn-terminal
PKG_CHECK_MODULES(VTE, [vte])

# awn-system-monitor, awn-notification-daemon, cairo-menu, filebrowser, plugger, trasher
if test "$with_gconf" != "no" -a "$config_backend" != "GConf"; then
  PKG_CHECK_MODULES(GCONF, [gconf-2.0])
  gconf=gconf-2.0
fi

if test "$with_gconf" != "no" -a "$with_gnome" != "no"; then
# filebrowser
PKG_CHECK_MODULES(GNOMEUI, [libgnomeui-2.0])
# filebrowser
PKG_CHECK_MODULES(GNOME_DESKTOP, [gnome-desktop-2.0])
# filebrowser, cairo-menu, plugger, trash, trasher
PKG_CHECK_MODULES(GNOME_VFS, [gnome-vfs-2.0])
# awn-system-monitor
PKG_CHECK_MODULES(GTOP, [libgtop-2.0])
fi

if test "$with_gnome" != "no"; then
# main-menu, cairo-menu
PKG_CHECK_MODULES(GNOME_MENU, [libgnome-menu])
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

# applet-specific libraries
if test "$with_gconf" != "no" -a "$with_gnome" != "no"; then
PKG_CHECK_MODULES(AWN_SYSTEM_MONITOR, [$gconf libgtop-2.0])
PKG_CHECK_MODULES(FILEBROWSER, [$gconf gnome-desktop-2.0 gnome-vfs-2.0 libgnomeui-2.0])
PKG_CHECK_MODULES(CAIRO_MENU_GNOME, [$gconf gnome-vfs-2.0 libgnome-menu libnotify $icon_entry_module])
PKG_CHECK_MODULES(PLUGGER, [$gconf gnome-vfs-2.0])
PKG_CHECK_MODULES(TRASH, [gnome-vfs-2.0 libglade-2.0 x11])
PKG_CHECK_MODULES(TRASHER, [$gconf gnome-vfs-2.0])
fi
if test "$with_gconf" != "no"; then
PKG_CHECK_MODULES(NOTIFICATION_DAEMON, [$gconf $gstreampkg libnotify $url_label_module libwnck-1.0 x11])
fi
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
    # battery-applet
    AM_CHECK_PYMOD(pynotify,,,AC_MSG_ERROR([python module pynotify required (python-notify)]))
    # arss, mail
    AM_CHECK_PYMOD(feedparser,,,AC_MSG_ERROR([python module feedparser required (python-feedparser)]))
    # cairo-clock
    AM_CHECK_PYMOD(rsvg,,,AC_MSG_ERROR([python module rsvg required (gnome-python-desktop)]))
    # cairo-clock, calendar
    AM_CHECK_PYMOD(dateutil,,,AC_MSG_ERROR([python module dateutil required (python-dateutil)]))
    if test "$with_gnome" != "no"; then
    # MiMenu, YAMA
    AM_CHECK_PYMOD(gmenu,,,AC_MSG_ERROR([python module gmenu required]))
    fi
    if test "$with_gconf" != "no" -o "$with_gnome" != "no"; then
    # stacks
    AM_CHECK_PYMOD(gnomedesktop,,,AC_MSG_ERROR([python module gnomedesktop required]))
    # stacks
    AM_CHECK_PYMOD(gnomevfs,,,AC_MSG_ERROR([python module gnomevfs required]))
    # stacks
    AM_CHECK_PYMOD(gnome.ui,,,AC_MSG_ERROR([python module gnome.ui required]))
    # awn-meebo, digg, pandora
    AM_CHECK_PYMOD(gtkmozembed,,,AC_MSG_ERROR([python module gtkmozembed required (python-gnome2-extras)]))
    fi
    if test "$with_gconf" != "no"; then
    # calendar, media-control, media-player, stacks
    AM_CHECK_PYMOD(gconf,,,AC_MSG_ERROR([python module gconf required]))
    # calendar
    AM_CHECK_PYMOD(gdata,,,AC_MSG_ERROR([python module gdata required (python-gdata)]))
    # media-player, volume-control
    AM_CHECK_PYMOD(gst,,,AC_MSG_ERROR([python module gstreamer required (python-gst0.10)]))
    # calendar
    AM_CHECK_PYMOD(vobject,,,AC_MSG_ERROR([python module gdata required (python-vobject)]))
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
has_vala=no
AWN_VAPIDIR=`$PKG_CONFIG --variable=vapidir awn`
if test -n "$AWN_VAPIDIR" -a -f "$AWN_VAPIDIR/awn.vapi"; then
    VALA_PROG_VALAC(0.5.4)
    AC_PATH_PROG(VAPIGEN, vapigen, vapigen, [])
    AC_SUBST(AWN_VAPIDIR)
    if test -n "$VALAC"; then
        has_vala=yes
    fi
fi
AM_CONDITIONAL(GCONF_SCHEMAS, test "$config_backend" = "GConf")
AM_CONDITIONAL(HAVE_VALA, test "$has_vala" = "yes")
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

appletsdir="$datarootdir/avant-window-navigator/applets"

AS_AC_EXPAND(APPLETSDIR, $appletsdir)
AS_AC_EXPAND(SYSCONFDIR, $sysconfdir)
AS_AC_EXPAND(LIBDIR, $libdir)
AS_AC_EXPAND(DATADIR, $datadir)
AS_AC_EXPAND(LIBEXECDIR, $libexecdir)

AC_DEFINE_UNQUOTED(APPLETSDIR, "$APPLETSDIR",
                   [The base directory for applet data and Python applets.])
AC_SUBST(APPLETSDIR)

DBUS_SERVICES_DIR=`$PKG_CONFIG --variable=session_bus_services_dir dbus-1`
AC_SUBST(DBUS_SERVICES_DIR)

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
src/animal-farm/Makefile
src/arss/Makefile
src/awn-meebo/Makefile
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
src/battery-applet/Makefile
src/cairo-clock/Makefile
src/cairo-menu/Makefile
src/cairo-menu/cairo_main_menu.desktop.in
src/calendar/Makefile
src/comic/Makefile
src/comics/Makefile
src/comics/locale/Makefile
src/comics/locale/sv_SE/Makefile
src/comics/locale/sv_SE/LC_MESSAGES/Makefile
src/cpufreq/Makefile
src/DesktopManager/Makefile
src/digg/Makefile
src/digitalClock/Makefile
src/file-browser-launcher/Makefile
src/filebrowser/Makefile
src/filebrowser/filebrowser.desktop.in
src/gwibfawn/Makefile
src/libawn-extras/Makefile
src/libawn-extras/awn-extras.pc
src/libawn-extras/bindings/Makefile
src/libawn-extras/bindings/python/defs.py
src/libawn-extras/bindings/python/Makefile
src/libawn-extras/bindings/vala/Makefile
src/mail/Makefile
src/mail/locale/Makefile
src/mail/locale/ru/Makefile
src/mail/locale/ru/LC_MESSAGES/Makefile
src/main-menu/Makefile
src/main-menu/main-menu.desktop.in
src/media-control/Makefile
src/media-icon-back/Makefile
src/media-icon-next/Makefile
src/media-icon-play/Makefile
src/media-player/Makefile
src/mount-applet/Makefile
src/MiMenu/Makefile
src/notification-area/Makefile
src/notification-area/notification-area.desktop.in
src/pandora/Makefile
src/places/Makefile
src/places/places.desktop.in
src/plugger/Makefile
src/plugger/plugger.desktop.in
src/pynot/Makefile
src/pynot-rgba/Makefile
src/python-test/Makefile
src/quit-applet/Makefile
src/rtm/Makefile
src/separator/Makefile
src/separator/separator.desktop.in
src/shiny-switcher/Makefile
src/shiny-switcher/shinyswitcher.desktop.in
src/showdesktop/Makefile
src/stacks/Makefile
src/sysmon/Makefile
src/sysmon/sysmon.desktop.in
src/thinkhdaps/Makefile
src/to-do/Makefile
src/tomboy-applet/Makefile
src/trash/Makefile
src/trash/trash.desktop.in
src/trasher/Makefile
src/trasher/trasher.desktop.in
src/vala-test/Makefile
src/vala-test/vala-test.desktop.in
src/volume-control/Makefile
src/weather/Makefile
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
src/webapplet/Makefile
src/webapplet/webapplet.desktop.in
src/wobblyzini/Makefile
src/wobblyzini/wobblyzini.desktop.in
src/yama/Makefile
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
echo "             Vala Support:   $has_vala"
echo ""
echo "           WebKit Support:   $webkit_module"
echo ""
