# /usr/bin/env python
import string
import os
import os.path as osp
def path_finder():
    a = 0
    paths = []
    temp = os.popen(r"echo $PATH")
    pathlist = temp.read()
    temp.close()
    while ':' in pathlist:
        paths.append(pathlist[:pathlist.index(':')])
        pathlist = pathlist.replace(paths[a] + ':','')
        a = a + 1
    paths.append(pathlist)
    pathlist = pathlist.replace(paths[a] + ':','')
    paths[-1] = string.rstrip(paths[-1])
    return paths
def exists(program):
    work = [False,None]
    if paths != None:
        for path in paths:
            test = path+'/'+program
            if osp.exists(test) == True:
                work = [True,test]
    return work
global paths
try:paths = path_finder()
except:paths=None
