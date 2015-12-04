#! /bin/sh
intltoolize -f -c || exit 1
autoreconf -vfi || exit 1
if test -z "$NOCONFIGURE"; then
	./configure --enable-maintainer-mode "$@"
fi
