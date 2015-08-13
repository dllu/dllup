#!/usr/bin/python

import os

def dfs(s):
    children = os.listdir(s)
    for child in children:
        zxcv = os.path.join(s, child)
        if child[-4:].lower() in ['.png']: 
            print('minifying %s' % zxcv)
            os.system('optipng -o6 "%s"' % zxcv)
        if child[-4:].lower() in ['.jpg', '.jpeg']:
            print('minifying %s' % zxcv)
            os.system('jpegoptim "%s" -s' % zxcv)
        if os.path.isdir(os.path.join(s,child)):
            dfs(zxcv)
dfs('site')
