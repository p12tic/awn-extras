CC=gcc
SRCS=pidgin_awn.c
OBJS=pidgin_awn.o
all:	gaim_awn.so

$(OBJS): ${SRCS}
	$(CC) -fPIC -Wall -c $(SRCS) -o ${OBJS} -DVERSION=\"`date "+%Y%m-%d_%R"`\" `pkg-config --cflags gtk+-2.0 pidgin purple atk cairo pango glib-2.0 dbus-1`

gaim_awn.so: $(OBJS)
	$(CC) -shared -Wl,-soname,pidgin_awn.so -o pidgin_awn.so $(OBJS)

install: pidgin_awn.so
	cp pidgin_awn.so /usr/lib/pidgin/

clean:
	rm pidgin_awn.so *.o

package:
	tar cvzf pidgin_awn-rev`svn info | grep Revision | sed 's/^Revision: //'`.tar.gz pidgin_awn.c pidgin_awn.so Makefile
