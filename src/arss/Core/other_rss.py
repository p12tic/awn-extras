def get_new_count(database, keye):
    count = 0
#    try:
    for feed in database:
        for story in database[feed][0]:
            if story['meta_read'] == keye:
                count += 1
#    except:print 'error: line 2 other.py'
    return count
