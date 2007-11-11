
import base64
import socket
import string
import lastfmexception
import sys

True = 1
False = 0

class httpclient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.status = None
        self.headers = None
        self.response = None

    def readline(self, s):
        res = ""
        while True:
            try:
                c = s.recv(1)
            except:
                break
            res = res + c
            if c == '\n':
                break
            if not c:
                break
        return res

    def req(self, url):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.send("GET " + url + " HTTP/1.0\r\n")
            s.send("Host: " + self.host + "\r\n")
            s.send("\r\n")
    
            line = self.readline(s)
            self.status = string.rstrip(line)
    
            self.headers = {}
            while True:
                line = self.readline(s)
                if not line:
                    break
                if line == "\r\n":
                    break
                tmp = string.split(line, ": ")
                self.headers[tmp[0]] = string.rstrip(tmp[1])
    
            self.response = ""
            while True:
                line = self.readline(s)
                if not line:
                    break
                self.response = self.response + line
            s.close()
        except:
            print "Unexpected error: ", sys.exc_info()[0]
            print "Unable to contact last.fm"
            raise lastfmexception.LastFmException(sys.exc_info()[0])

