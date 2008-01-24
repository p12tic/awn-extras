#! /bin/sh
intltoolize -f || exit 1
autoreconf -v --install || exit 1
if test -z "$NOCONFIGURE"; then
	./configure --enable-maintainer-mode "$@"
fi
