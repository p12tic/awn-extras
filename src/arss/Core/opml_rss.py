import sys
import xml.dom.minidom
from xml.dom.minidom import Node

def feeds_from_opml(file):
    doc = xml.dom.minidom.parse(file)
    out = []
    for node in doc.getElementsByTagName("outline"):
        url = node.getAttribute("xmlUrl")
        if 'http://' in url:
            out.append(url)
    return out
        
if __name__ == '__main__':
    for item in feeds_from_opml(sys.argv[1]):
        print item
