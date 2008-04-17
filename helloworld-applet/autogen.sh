#! /bin/sh
intltoolize -f || exit 1
autoreconf -v --install || exit 1
./configure --enable-maintainer-mode "$@"
