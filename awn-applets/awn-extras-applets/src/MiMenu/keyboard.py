# !/usr/bin/env python

def navigate(widget,event=None,tree=None,treeswitch=None):
    """
    Controls keyboard nav
    """
    if treeswitch == 1:
        if event != None:
            if event.keyval == 65363:
                tree.set_cursor((0,0))
                tree.grab_focus()
    elif treeswitch == 2:
        if event != None:
            if event.keyval == 65361:
                tree.grab_focus()
def tree2faux(widget,event,treeclick,tree2,obj,
              path=None,viewcolumn=None,keyclick=False):
    try:button = event.button
    except:button = None
    if button == 1 or keyclick==True:
        treeclick(widget,tree2,obj,True)
def tree2activated(widget,x,y,treeclick,tree,obj):
    if str(tree.get_cursor())[2] == '0':
        treeclick(widget,tree,obj,True,t2act=True)
    else:treeclick(widget,tree,obj,True)
