APPLET_NAME = cpufreq
APPLET_MAIN_FILE = cpufreq.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA =	\
	cpufreq.svg	\
	cpufreq.ui	\
	$(NULL)

imagesdir = $(applet_datadir)/images
dist_images_DATA = $(wildcard $(srcdir)/images/cpufreq-*.svg)

theme_moonbeamdir = $(applet_datadir)/themes/moonbeam
dist_theme_moonbeam_DATA =           \
    themes/moonbeam/index.theme \
    $(NULL)

theme_scalable_moonbeamdir = $(applet_datadir)/themes/moonbeam/scalable
dist_theme_scalable_moonbeam_DATA =          \
    themes/moonbeam/scalable/cpufreq-0.svg  \
    themes/moonbeam/scalable/cpufreq-1.svg \
    themes/moonbeam/scalable/cpufreq-2.svg \
    themes/moonbeam/scalable/cpufreq-3.svg \
    themes/moonbeam/scalable/cpufreq-4.svg \
    themes/moonbeam/scalable/cpufreq-5.svg \
    themes/moonbeam/scalable/cpufreq-6.svg \
    themes/moonbeam/scalable/cpufreq-7.svg \
    themes/moonbeam/scalable/cpufreq-8.svg \
    themes/moonbeam/scalable/cpufreq-9.svg \
    themes/moonbeam/scalable/cpufreq-10.svg \
    themes/moonbeam/scalable/cpufreq-11.svg \
    themes/moonbeam/scalable/cpufreq-12.svg \
    themes/moonbeam/scalable/cpufreq-13.svg    \
    $(NULL)
