APPLET_NAME = hardware-sensors
APPLET_MAIN_FILE = hardware-sensors.py
include $(top_srcdir)/Makefile.python-applet
include $(top_srcdir)/Makefile.schemas

dist_applet_DATA =	\
	sensoricon.py	\
	hardware-sensors.ui		\
	$(NULL)

interfacesdir = $(applet_datadir)/interfaces
dist_interfaces_DATA =				\
	interfaces/__init__.py			\
	interfaces/acpisensors.py		\
	interfaces/fileinterface.py		\
	interfaces/hddtempsensors.py	\
	interfaces/lmsensors.py			\
	interfaces/nvclocksensors.py	\
	interfaces/nvidiasensors.py		\
	interfaces/omnibooksensors.py	\
	interfaces/sensorinterface.py	\
	$(NULL)

sensorvaluesdir = $(applet_datadir)/sensorvalues
dist_sensorvalues_DATA =		\
	sensorvalues/__init__.py	\
	sensorvalues/rpmvalue.py	\
	sensorvalues/sensorvalue.py	\
	sensorvalues/tempvalue.py	\
	sensorvalues/units.py		\
	sensorvalues/voltvalue.py	\
	$(NULL)

imagesdir = $(applet_datadir)/images
dist_images_DATA =			\
	images/no_sensors.svg	\
	images/thermometer.png	\
	images/thermometer.svg	\
	$(NULL)

applet_imagesdir = $(applet_datadir)/images/applet
dist_applet_images_DATA =					\
	images/applet/dark-bg.png		\
	images/applet/dark_shiny_border.svg	\
	images/applet/dark_shiny.svg			\
	images/applet/dark.svg					\
	images/applet/light-bg.png		\
	images/applet/light_shiny_border.svg	\
	images/applet/light_shiny.svg			\
	images/applet/light.svg					\
	images/applet/transparent_border.svg	\
	images/applet/transparent.svg			\
	$(NULL)

