import os
import os.path
from settings_rss import *
import cPickle

def save_database(database, file = Settings.__database_file__):
    file = open(file, 'w')
    cPickle.dump(database, file)
    file.close()
    return True

def load_database(file = Settings.__database_file__):
    if os.path.exists(file) == False:
        return False
    else:
        file = open(file, 'r')
        database = cPickle.load(file)
        file.close()
        return database
