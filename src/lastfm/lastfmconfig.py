import gconf
import md5

class LastFmConfiguration:
    #username
    #password
    #icon
    
    def __init__(self):
        self.gconf_path = "/apps/avant-window-navigator/applets/lastfm"
        self.gconf_client = gconf.client_get_default()
    
    def set_username(self, value):
        self.gconf_client.set_string(self.gconf_path + "/username", value)
        return value
        
    def get_username(self):
        username = self.gconf_client.get_string(self.gconf_path + "/username")
        if username == None:
            username = ""
            
        return username
    
    def set_password(self, value):
        md5_password = md5.md5(value).hexdigest()
        self.gconf_client.set_string(self.gconf_path + "/password", md5_password)
        return md5_password
    
    def get_password(self):
        passwd = self.gconf_client.get_string(self.gconf_path + "/password")
        if passwd == None:
            passwd = ""
            
        return passwd
    
    def get_icon(self):
        icon = self.gconf_client.get_string(self.gconf_path + "/icon")
        if icon == None:
            icon = "red.ico"
        return icon
    
    def set_icon(self, value):
        self.gconf_client.set_string(self.gconf_path + "/icon", value)
        return value
    
    #def set_last_station_