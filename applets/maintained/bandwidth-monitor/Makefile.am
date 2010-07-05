APPLET_NAME = bandwidth-monitor
APPLET_MAIN_FILE = awn-bwm.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA =	\
	CHANGELOG   \
	bwmprefs.py \
	bandwidth-monitor.ui \
	interfaces_dialog.py \
	$(NULL)

bwm_iconsdir = $(applet_datadir)/images
dist_bwm_icons_DATA =           \
	images/bluetooth.png        \
	images/ethernet.png         \
	images/icon.png             \
	images/loopback.png         \
	images/multi.png            \
	images/sum.png              \
	images/tun-tap.png          \
	images/wireless-disconnected.png    \
	images/wireless-full.png    \
	images/wireless-high.png    \
	images/wireless-low.png     \
	images/wireless-medium.png  \
	$(NULL)

