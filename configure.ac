SAC_PREREQ(2.53)

m4_define(pycairo_required_version,      1.0.2) dnl or 1.1.7
m4_define(pygtk_required_version,        2.10.0)


AC_INIT(awn-extras-applets, 0.3.9, [])
AM_INIT_AUTOMAKE([-Wno-portability])
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_SRCDIR(applets)
AM_CONFIG_HEADER(config.h)
AM_MAINTAINER_MODE

AC_ISC_POSIX
AC_PROG_CC
AC_STDC_HEADERS
AC_PROG_LIBTOOL
DOLT

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
dnl Python script installation
dnl

AC_PYTHON_DEVEL

dnl
dnl library support
dnl

AC_CHECK_LIB(m, round)
# shiny-switcher
PKG_CHECK_EXISTS([libwnck-1.0 >= 2.21.99.9], [AC_DEFINE(HAVE_LIBWNCK_222, 1, [Have libwnck 2.22.x])])


dnl
dnl package support
dnl

AC_ARG_WITH([gconf], AS_HELP_STRING([--without-gconf],[Disable building/installing applets that need GConf]),,[with_gconf=yes])
AC_ARG_WITH([gnome], AS_HELP_STRING([--without-gnome],[Disable building/installing applets that require Gnome-specific libraries]),,[with_gnome=yes])
AC_ARG_WITH([mozilla], AS_HELP_STRING([--with-mozilla],[Enable building/installing applets that require Gecko (Mozilla)]),,[with_mozilla=no])
AC_ARG_WITH([webkit], AS_HELP_STRING([--with-webkit],[Enable building/installing applets that require webkitgtk]),,[with_webkit=no])
AM_CONDITIONAL(WITH_GCONF, test "$with_gconf" != "no")
AM_CONDITIONAL(WITH_GNOME, test "$with_gnome" != "no")
AM_CONDITIONAL(WITH_MOZILLA, test "$with_mozilla" != "no")
AM_CONDITIONAL(WITH_WEBKIT, test "$with_webkit" != "no")
AM_CONDITIONAL(BUILD_WEBAPPLET, test "$with_mozilla" != "no" -o "$with_webkit" != "no")

# all
PKG_CHECK_MODULES(AWN, [awn >= 0.3.9])
#trash
#PKG_CHECK_MODULES(LIBGLADE, [libglade-2.0])
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
# awn-terminal
PKG_CHECK_MODULES(VTE, [vte])

# awn-system-monitor, awn-notification-daemon, cairo-menu, filebrowser, plugger, trasher
if test "$with_gconf" != "no"; then
  PKG_CHECK_MODULES(GCONF, [gconf-2.0])
  gconf=gconf-2.0
fi

#if test "$with_gconf" != "no" -a "$with_gnome" != "no"; then
# filebrowser
#PKG_CHECK_MODULES(GNOMEUI, [libgnomeui-2.0])
# filebrowser
#PKG_CHECK_MODULES(GNOME_DESKTOP, [gnome-desktop-2.0])
# filebrowser, cairo-menu, plugger, trash, trasher
#PKG_CHECK_MODULES(GNOME_VFS, [gnome-vfs-2.0])
#fi

if test "$with_gnome" != "no"; then
# main-menu, cairo-menu
PKG_CHECK_MODULES(GNOME_MENU, [libgnome-menu])
# awn-system-monitor, sysmon
PKG_CHECK_MODULES(GTOP, [libgtop-2.0])
fi

# webapplet
webapplet_modules=""
mozilla_module=no
if test "$with_mozilla" != "no"; then
    found_mozilla=no
    for p in mozilla firefox xulrunner seamonkey; do
        mozilla_module="${p}-gtkmozembed"
        PKG_CHECK_EXISTS([$mozilla_module],[found_mozilla=yes])
        if test "$found_mozilla" = "yes"; then
            break
        fi
    done
    if test "$found_mozilla" = "yes"; then
        AC_DEFINE([HAVE_MOZILLA],[1],[Define if Gecko (Mozilla) is available.])
        webapplet_modules="$webapplet_modules $mozilla_module"
    else
        AC_MSG_ERROR([Could not find Gecko's gtkmozembed (needed for Mozilla support)])
    fi
fi

webkit_module=no
if test "$with_webkit" != "no"; then
PKG_CHECK_EXISTS([webkit-1.0],[webkit_module="webkit-1.0"],
    [PKG_CHECK_EXISTS([WebKitGtk],[
        webkit_module="WebKitGtk"
        AC_DEFINE([HAVE_OLD_WEBKITGTK],[1],[Define if the installed WebKit uses the old pkgconfig file and header structure.])
        ],[AC_MSG_ERROR([Could not find packages webkit-1.0 or WebKitGtk.  Either one is required for webkit support to be enabled.])])])
AC_DEFINE([HAVE_WEBKIT],[1],[Define if WebKit is available.])
webapplet_modules="$webapplet_modules $webkit_module"
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
#PKG_CHECK_MODULES(FILEBROWSER, [$gconf gnome-desktop-2.0 gnome-vfs-2.0 libgnomeui-2.0])
PKG_CHECK_MODULES(CAIRO_MENU_GNOME, [$gconf libgnome-menu libnotify $icon_entry_module])
#PKG_CHECK_MODULES(PLUGGER, [$gconf gnome-vfs-2.0])
#PKG_CHECK_MODULES(TRASH, [gnome-vfs-2.0 libglade-2.0 x11])
#PKG_CHECK_MODULES(TRASHER, [$gconf gnome-vfs-2.0])
fi
if test "$with_gconf" != "no"; then
PKG_CHECK_MODULES(NOTIFICATION_DAEMON, [$gconf $gstreampkg libnotify $url_label_module libwnck-1.0 x11])
fi
PKG_CHECK_MODULES(SHINY_SWITCHER, [libwnck-1.0 x11 xcomposite xrender])
if test -n "$webapplet_modules"; then
    PKG_CHECK_MODULES(WEBAPPLET, [$webapplet_modules])
fi

dnl
dnl Check python modules
dnl
AC_ARG_ENABLE(pymod_checks,
              AC_HELP_STRING([--disable-pymod-checks], [Disable checks for Python modules]),
              enable_pymod_checks=$enableval,
              enable_pymod_checks=yes)

if test x${enable_pymod_checks} = xyes; then
    # awnlib, battery-applet, DesktopManager, pynot, pynot-rgba
    AM_CHECK_PYMOD(pynotify,,,AC_MSG_ERROR([python module pynotify required (python-notify)]))
    # arss, feeds, mail
    AM_CHECK_PYMOD(feedparser,,,AC_MSG_ERROR([python module feedparser required (python-feedparser)]))
    # cairo-clock
    AM_CHECK_PYMOD(rsvg,,,AC_MSG_ERROR([python module rsvg required (gnome-python-desktop)]))
    # cairo-clock, calendar
    AM_CHECK_PYMOD(dateutil,,,AC_MSG_ERROR([python module dateutil required (python-dateutil)]))
    # media-player, volume-control
    AM_CHECK_PYMOD(gst,,,AC_MSG_ERROR([python module gstreamer required (python-gst0.10)]))
    if test "$with_gnome" != "no"; then
    # MiMenu, YAMA
    AM_CHECK_PYMOD(gmenu,,,AC_MSG_ERROR([python module gmenu required]))
    fi
    #if test "$with_gconf" != "no" -o "$with_gnome" != "no"; then
    # stacks
#    AM_CHECK_PYMOD(gnomedesktop,,,AC_MSG_ERROR([python module gnomedesktop required]))
    # stacks
#    AM_CHECK_PYMOD(gnomevfs,,,AC_MSG_ERROR([python module gnomevfs required]))
    # stacks
#    AM_CHECK_PYMOD(gnome.ui,,,AC_MSG_ERROR([python module gnome.ui required]))
    # awn-meebo, digg, pandora
#    AM_CHECK_PYMOD(gtkmozembed,,,AC_MSG_ERROR([python module gtkmozembed required (python-gnome2-extras)]))
    #fi
    if test "$with_gconf" != "no"; then
    # calendar, media-control, media-player, stacks
    AM_CHECK_PYMOD(gconf,,,AC_MSG_ERROR([python module gconf required]))
    # calendar
    AM_CHECK_PYMOD(gdata,,,AC_MSG_ERROR([python module gdata required (python-gdata)]))
    # calendar
    AM_CHECK_PYMOD(vobject,,,AC_MSG_ERROR([python module gdata required (python-vobject)]))
    fi
fi

dnl
dnl Determine the location of lda-schema-to-gconf
dnl

LDA_BINDIR=`$PKG_CONFIG --variable=exec_prefix desktop-agnostic`/bin
AC_SUBST(LDA_BINDIR)

dnl
dnl Check for Vala support.
dnl
has_vala=no
LDA_VAPIDIR=`$PKG_CONFIG --variable=vapidir desktop-agnostic`
AWN_VAPIDIR=`$PKG_CONFIG --variable=vapidir awn`
if test -n "$LDA_VAPIDIR" -a -n "$AWN_VAPIDIR" -a -f "$AWN_VAPIDIR/awn.vapi"; then
    VALA_PROG_VALAC(0.5.4)
    AC_SUBST(LDA_VAPIDIR)
    AC_SUBST(AWN_VAPIDIR)
    if test -n "$VALAC"; then
        has_vala=yes
    fi
fi
AM_CONDITIONAL(HAVE_VALA, test "$has_vala" = "yes")

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

AM_GCONF_SOURCE_2
if test "$enable_schemas_install" != "no"; then
  AC_PATH_PROG(GCONFTOOL, gconftool-2, no)
  if test x"$GCONFTOOL" = xno; then
    AC_MSG_ERROR([gconftool-2 executable not found in your path - should be installed with GConf])
  fi
fi


dnl ==========================
dnl Shave (quiet build output)
dnl ==========================

SHAVE_INIT([shave], [enable])

dnl Please keep in alphabetical order
AC_OUTPUT([
Makefile
applets/Makefile
applets/maintained/animal-farm/Makefile
applets/maintained/awnsystemmonitor/Makefile
applets/maintained/awnsystemmonitor/awnsystemmonitor.desktop.in
applets/maintained/awnterm/Makefile
applets/maintained/awnterm/awnterm.desktop.in
applets/maintained/battery-applet/Makefile
applets/maintained/cairo-clock/Makefile
applets/maintained/cairo-menu/Makefile
applets/maintained/cairo-menu/cairo_main_menu.desktop.in
applets/maintained/calendar/Makefile
applets/maintained/comics/Makefile
applets/maintained/comics/locale/Makefile
applets/maintained/comics/locale/sv_SE/Makefile
applets/maintained/comics/locale/sv_SE/LC_MESSAGES/Makefile
applets/maintained/cpufreq/Makefile
applets/maintained/digitalClock/Makefile
applets/maintained/feeds/Makefile
applets/maintained/file-browser-launcher/Makefile
applets/maintained/gwibfawn/Makefile
applets/maintained/media-control/Makefile
applets/maintained/media-icons/Makefile
applets/maintained/media-icons/media-icon-next.desktop.in
applets/maintained/media-icons/media-icon-previous.desktop.in
applets/maintained/media-player/Makefile
applets/maintained/mount-applet/Makefile
applets/maintained/notification-area/Makefile
applets/maintained/notification-area/notification-area.desktop.in
applets/maintained/notification-daemon/Makefile
applets/maintained/notification-daemon/awnnotificationdaemon.desktop.in
applets/maintained/places/Makefile
applets/maintained/places/places.desktop.in
applets/maintained/python-test/Makefile
applets/maintained/quit-applet/Makefile
applets/maintained/rtm/Makefile
applets/maintained/shiny-switcher/Makefile
applets/maintained/shiny-switcher/shinyswitcher.desktop.in
applets/maintained/showdesktop/Makefile
applets/maintained/sysmon/Makefile
applets/maintained/sysmon/sysmon.desktop.in
applets/maintained/thinkhdaps/Makefile
applets/maintained/to-do/Makefile
applets/maintained/tomboy-applet/Makefile
applets/maintained/vala-test/Makefile
applets/maintained/vala-test/vala-test.desktop.in
applets/maintained/volume-control/Makefile
applets/maintained/weather/Makefile
applets/maintained/weather/locale/Makefile
applets/maintained/weather/locale/es/Makefile
applets/maintained/weather/locale/es/LC_MESSAGES/Makefile
applets/maintained/weather/locale/fr/Makefile
applets/maintained/weather/locale/fr/LC_MESSAGES/Makefile
applets/maintained/weather/locale/nb/Makefile
applets/maintained/weather/locale/nb/LC_MESSAGES/Makefile
applets/maintained/weather/locale/nn/Makefile
applets/maintained/weather/locale/nn/LC_MESSAGES/Makefile
applets/maintained/weather/locale/pt/Makefile
applets/maintained/weather/locale/pt/LC_MESSAGES/Makefile
applets/maintained/webapplet/Makefile
applets/maintained/webapplet/webapplet.desktop.in
applets/maintained/wobblyzini/Makefile
applets/maintained/wobblyzini/wobblyzini.desktop.in
applets/maintained/yama/Makefile
applets/unmaintained/arss/Makefile
applets/unmaintained/awn-meebo/Makefile
applets/unmaintained/comic/Makefile
applets/unmaintained/DesktopManager/Makefile
applets/unmaintained/digg/Makefile
applets/unmaintained/filebrowser/Makefile
applets/unmaintained/filebrowser/filebrowser.desktop.in
applets/unmaintained/mail/Makefile
applets/unmaintained/mail/locale/Makefile
applets/unmaintained/mail/locale/ru/Makefile
applets/unmaintained/mail/locale/ru/LC_MESSAGES/Makefile
applets/unmaintained/main-menu/Makefile
applets/unmaintained/main-menu/main-menu.desktop.in
applets/unmaintained/MiMenu/Makefile
applets/unmaintained/pandora/Makefile
applets/unmaintained/plugger/Makefile
applets/unmaintained/plugger/plugger.desktop.in
applets/unmaintained/pynot/Makefile
applets/unmaintained/pynot-rgba/Makefile
applets/unmaintained/separator/Makefile
applets/unmaintained/separator/separator.desktop.in
applets/unmaintained/stacks/Makefile
applets/unmaintained/trash/Makefile
applets/unmaintained/trash/trash.desktop.in
applets/unmaintained/trasher/Makefile
applets/unmaintained/trasher/trasher.desktop.in
po/Makefile.in
shared/python/defs.py
shared/python/Makefile
shave/shave
shave/shave-libtool
])

dnl ========================================================================

echo ""
echo "         Avant Window Navigator Extras $VERSION"
echo "         ==================================="
echo ""
echo "                   prefix:   ${prefix}"
echo ""
echo "             Vala Support:   $has_vala"
echo ""
echo "           WebKit Support:   $webkit_module"
echo ""
echo "            Gecko Support:   $mozilla_module"
echo ""
