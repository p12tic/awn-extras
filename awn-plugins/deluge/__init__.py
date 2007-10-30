plugin_name = _("Awn Deluge")
plugin_author = "Alberto Munnoz"
plugin_version = "0.5"
plugin_description = _("This plugin prints the download rate and the upload rate on AWN dock")


def deluge_init(deluge_path):
    global path
    path = deluge_path

from AwnDeluge.plugin import plugin_AwnDeluge

def enable(core, interface):
    global path
    return plugin_AwnDeluge(path, core, interface)
