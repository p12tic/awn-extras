
#include "sysmon.h"



AwnApplet* awn_applet_factory_initp(gchar* uid, gint orient, gint offset, gint height)
{
  AwnApplet *applet = AWN_APPLET(awn_sysmon_new(uid, orient, offset, height));

  return applet;
}

