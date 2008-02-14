import httpclient
import time
import string
import urllib

class lastfm:

    def __init__(self):
        self.version = "0.31"
        self.platform = "linux"
        self.host = "ws.audioscrobbler.com"
        self.port = 80
        #self.state = 0
        self.info = None
        self.metadata = dict()
        #self.metadatatime = 0
        self.progress = 0

    def parselines(self, str):
        res = {}
        vars = string.split(str, "\n")
        for v in vars:
            x = string.split(string.rstrip(v), "=", 1)
            if len(x) == 2:
                res[x[0]] = x[1]
            elif x != [""]:
                print "(urk?", x, ")"
        return res

    def connect(self, username, password):
        s = httpclient.httpclient(self.host, self.port)
        s.req("/radio/handshake.php?version=" + self.version + "&platform=" + self.platform + "&username=" + username + "&passwordmd5=" + password)

        self.info = self.parselines(s.response)

        #self.state = 1
        
        print "status:", repr(s.status)
        #print "headers:", repr(s.headers)
        print "info:", repr(self.info)

        if self.info["session"] == "FAILED":
           return 1
        else:
           return 0

    def command(self, cmd):
        # commands = skip, love, ban, rtp, nortp
        s = httpclient.httpclient(self.info["base_url"], 80)
        s.req(self.info["base_path"] + "/control.php?command=" + cmd + "&session=" + self.info["session"])
        res = self.parselines(s.response)
        if res["response"] != "OK":
            print "command " + cmd + " returned:", res
        return res["response"]

    def changestation(self, station_type, station_name):
        if station_type == "similarartists":
            url = "lastfm://artist/" + station_name + "/similarartists"
            station_desc = station_name + "'s Similar Artists"
	elif station_type == "group":
            url = "lastfm://group/" + station_name
            station_desc = station_name + " Group Radio"
        elif station_type == "tag":
            url = "lastfm://globaltags/" + station_name
            station_desc = station_name + " Tag Radio"
        elif station_type == "personal":
            url = "lasfm://user/" + station_name + "/personal"
            station_desc = station_name + "'s Music"
         
        url = urllib.quote(url) # fixes bug for artists with spaces in names, thanks to Mike (mosburger) Desjardins <desjardinsmike@gmail.com>

        print url

        s = httpclient.httpclient(self.info["base_url"], 80)
        s.req(self.info["base_path"] + "/adjust.php?session=" + self.info["session"] + "&url=" + url)
        res = self.parselines(s.response)
        
        if res["response"] != "OK":
            print "station " + url + " returned:", res
            return False
        
        return station_desc

    def getmetadata(self):
        s = httpclient.httpclient(self.info["base_url"], 80)
        s.req(self.info["base_path"] + "/np.php?session=" + self.info["session"])
        tmp = self.parselines(s.response)

        if 1:
            # Dump metadata to files. For debugging.
            f = open("/tmp/metadata-" + str(time.time()) + ".txt", "w")
            f.write(repr(tmp))
            f.close()

        if tmp.has_key('\xef\xbb\xbfstreaming'):
            tmp["streaming"] = tmp['\xef\xbb\xbfstreaming']

        if tmp.has_key("streaming"):
            if tmp["streaming"] == "false" or (tmp["streaming"] == "true" and tmp.has_key("artist") and tmp.has_key("track") and tmp.has_key("trackduration")):
                if not tmp.has_key("album"):
                    tmp["album"] = ""
                    tmp["album_url"] = ""
                self.metadata = tmp
                #self.metadatatime = time.time()
                return 1
        print "getmetadata: got funky metadata:", repr(tmp)
        return 0
    
    def get_cover_url(self):
        imageurl = False
        if self.metadata.has_key('albumcover_medium'):
            imageurl = self.metadata['albumcover_medium']
        elif self.metadata.has_key('albumcover_small'):
            imageurl = self.metadata['albumcover_small']
        elif self.metadata.has_key('albumcover_big'):
            imageurl = self.metadata['albumcover_big']
        return imageurl
