import os.path
import sys


class Settings(object):
    __database_file__ = os.path.expanduser('~') +\
                         '/.config/awn/applets/.awnrss0.99c.feeddatabase'
    __reload_time__ = 3600
    __MAX_ENTRIES__ = 30
    __feedsfile__ = os.path.expanduser('~') + '/.config/awn/applets/.feedlist'
    __location__ = __file__[::-1][__file__[::-1].index('/'):][::-1]
    __feed_icon__ = __location__ + 'feed-icon.svg'
    __feed_icon_gray__ = __location__ + 'feed-icon-gray.svg'
    __feed_icon_unread__ = __location__ + 'feed-icon-unread.png'
    __feed_icon_new__ = __location__ + 'feed-icon-new.png'
