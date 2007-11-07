README - How to activate unstable applet
========================================

If you want to activate unstable applets, enter in awn-extras/awn-applets directory and do :

patch -p0 < activate-unstable-applet.patch

If you want to disable unstable applets, do :

patch -Rp0 < activate-unstable-applet.patch

After, compiling as normal

RELEASE Notes
=============
To start meebo and digg applets, you must install gtkmozembed, and add

/usr/lib/firefox 

to the end of the file /etc/ld.so.conf then run ldconfig

