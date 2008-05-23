import os
import sys
import feedparser
try:
    import feedparserdb
    import arssconfig
except ImportError:
    print "feedparser test mode only"

userpath = os.path.expanduser('~/')
test_uris = ['http://www.userfriendly.org/rss/uf.rss',
             'http://planet.ubuntu.com/rss20.xml']

def  _publication_date_check(entries):
    isupdatable = True
    while isupdatable == True:
        for entry in entries:
            if 'updated_parsed' not in entry.keys():
                isupdatable = False
        break
    return isupdatable

def feed_test(uris = test_uris):
    obj = [feedparser.parse(uri).entries for uri in uris]    
    for feedentries in obj:
        print _publication_date_check(feedentries)

def feedparserdbtest():
    feeds = arssconfig.get_feeds()
    db = feedparserdb.FeedDatabase("sqlite:///"+userpath+"/.config/awn/arsstest.db", echo=False)
    db.update_feeds(feeds+[test_uris[0]])
    for feed in db.get_feed_objects():
        print feed.URI + " Pubdated?: " + str(_publication_date_check(feed.Entries))
        

if __name__ == "__main__":
    if 'database' in sys.argv:
        feedparserdbtest()
    else:
        feed_test()
        