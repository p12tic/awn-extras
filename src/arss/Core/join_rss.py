# !/usr/bin/python
# -*- coding: utf-8 -*-

def compare_by(fieldname):
    def compare_two_dicts (a, b):
        return cmp(a[fieldname], b[fieldname])
    return compare_two_dicts

def sortit(L):
    if L:
        L.sort(compare_by('title'))
        last = L[-1]
        for i in range(len(L)-2, -1, -1):
            if last['title'] == L[i]['title']:
                del L[i]
            else:
                last = L[i]
    return L

def merge(old, new):
    for story in new:
        story['meta_read'] = None
    for story in old:
        if story['meta_read'] == None:
            story['meta_read'] = False
    mix = new + old
    final = sortit(mix)
    try:
        final.sort(compare_by('updated_parsed'))
    except:
        final.sort(compare_by('title'))
    final = final[::-1]
    return final

def merge_db(old, new):
    final = {}
    count = 0
    i = 0
    for key in new:
        if key not in old.keys():
            final[key] = new[key]
            for story in new[key][0]:
                story['meta_read'] = None

    for feed in old:
        if feed in new.keys():
            new_db = merge(old[feed][0], new[feed][0])
            if i < 0: i = 0
            final[feed] = [new_db, old[feed][1]]
            count += i
    return final
