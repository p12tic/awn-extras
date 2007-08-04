AC_PREREQ(2.53)
AC_INIT(awn-core-applets, 0.1, [])
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

GETTEXT_PACKAGE=awn-core-applets
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
                  libgnome-menu 
                  gnome-desktop-2.0
                  librsvg-2.0)
AC_SUBST(DEPS_CFLAGS)
AC_SUBST(DEPS_LIBS)

if test "x$GCC" = "xyes"; then
        GCC_FLAGS="-g -Wall"
fi

AC_SUBST(GCC_FLAGS)

dnl Please keep in alpha order
AC_OUTPUT([
Makefile
po/Makefile.in
src/Makefile
src/clock/Makefile
src/main-menu/Makefile
src/wobblyzini/Makefile
])
