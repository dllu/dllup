#!/usr/bin/python
# The templating engine and the parser for the dllup markup language are hereby
# released open-source under the MIT License.
#
# Copyright (c) 2015 Daniel Lawrence Lu

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import dllup
import hashlib
import os
import re
import struct
import time
from operator import itemgetter

RASTER_IMG = ['.png', '.jpg']
# navigation markup
PORTFOLIO_NAV = '<a href="{child}/"><figure><img src="{pic}" alt="{child}"/><figcaption>{title} ({subtitle})</figcaption></figure></a>'
BLOG_NAV = '<a href="{child}/"><span class="blogdate">{date}</span><span class="blogtitle">{title}</span></a>'
ROOT_NAV = '<a href="/{child}/">{child}</a>'
# the first breadcrumb
BREAD = '<a href="/"><span id="dllu"><span style="display:none;">dllu</span><span id="D"></span><span id="L0"></span><span id="L1"></span><span id="U"></span></span></a><span>/</span>'
BREAD_HERO = '<a href="/" id="hero-a"><span id="dllu-hero"><span style="display:none;">dllu</span><span id="D"></span><span id="L0"></span><span id="L1"></span><span id="U"></span></span></a>'
# all consecutive breadcrumbs
CRUMB = '<a href="{cpath}">{child}</a><span>/</span>'

# page markup
PAGE = '<!DOCTYPE html>\n{sig}\n{htmlhead}<nav id="breadcrumbs">{breadcrumbs}</nav><nav id="rootnav">{rootnav}</nav><nav id="{navtype}">{nav}</nav><main>{output}<footer><p>&copy; Daniel Lawrence Lu. Page generated on {time} by <a href="/programming/dllup/">dllup</a>. (<a href="{text}">text version</a>)</footer></main>{htmlfoot}'
PAGE_HERO = PAGE.replace('id="breadcrumbs"', 'id="hero"')


def readconfig(configpath):
    # Reads a config file which is a simple text file of key-value pairs.
    # One key-value pair per line, key (no whitespaces) is separated from
    # value by whitespace.
    # Valid keys are: type, root
    if not os.path.exists(configpath):
        return {}
    config = open(configpath).read()
    configsplit = [cc.split(None, 1) for cc in config.split('\n')]
    return {c[0]: c[1] for c in configsplit if len(c) >= 2}


def recurse(path='', rootnav='', root=''):
    global htmlhead
    global htmlfoot
    children = os.listdir(path)
    folderdata = [
        get_folderdata(os.path.join(path, c)) for c in children
        if os.path.isdir(os.path.join(path, c))
    ]
    config = readconfig(os.path.join(path, 'config'))
    if 'root' in config:
        root = config['root']
    navtype = config['type'] if 'type' in config else None
    # generate navigation markup
    nav = ''
    if navtype == 'blogposts':
        folderdata = sorted(
            [f for f in folderdata if 'date' in f],
            key=itemgetter('date'),
            reverse=True,
        )
    elif navtype == 'portfolio':
        folderdata = sorted(
            [f for f in folderdata if 'subtitle' in f],
            key=itemgetter('subtitle'),
            reverse=True,
        )
    else:
        folderdata = sorted([f for f in folderdata if 'child' in f],
                            key=itemgetter('child'))
    for f in folderdata:
        try:
            if navtype == 'root':
                rootnav += ROOT_NAV.format(**f)
            elif navtype == 'blogposts':
                nav += BLOG_NAV.format(**f)
            elif navtype == 'portfolio':
                nav += PORTFOLIO_NAV.format(**f)
        except KeyError:
            pass  # ignore folders without complete data

    breadcrumbs = crumbify(path)
    # recurse through children
    for child in children:
        cpath = os.path.join(path, child)
        if os.path.isdir(cpath):
            recurse(cpath, rootnav, root)
        if child[-4:] in RASTER_IMG and not '_600' in child:
            resize_images(path, child)
            pass
        elif child[-5:] == '.dllu':
            markup = open(os.path.join(path, child)).read()
            sig = '<!--%s-->' % hashlib.sha1(
                struct.pack('f', os.path.getmtime(cpath))).hexdigest()
            sig2 = None
            try:
                with open(os.path.join(path, child[:-5] + '.html')) as f:
                    f.readline()
                    sig2 = f.readline()
            except FileNotFoundError:
                pass
            if sig == sig2:
                continue

            output = dllup.parse(markup)
            f = open(os.path.join(path, child[:-5] + '.html'), 'w')
            PP = PAGE
            if path == '.':
                PP = PAGE_HERO

            f.write(
                PP.format(htmlhead=htmlhead,
                          htmlfoot=htmlfoot,
                          breadcrumbs=breadcrumbs,
                          rootnav=rootnav,
                          navtype=navtype,
                          output=output,
                          time=time.strftime('%Y-%m-%d', time.gmtime()),
                          child=child,
                          nav=nav,
                          sig=sig,
                          text=child).replace(
                              ' src="/',
                              ' src="%s/' % root,
                          ).replace(
                              ' href="/',
                              ' href="%s/' % root,
                          ))
            f.close()


def resize_images(path, child):
    filename = os.path.join(path, child)
    filename600 = os.path.join(path, child[:-4] + '_600' + child[-4:])
    filename600x2 = os.path.join(path, child[:-4] + '_600@2x' + child[-4:])
    for f in (filename600, filename600x2):
        if not os.path.exists(f):
            os.system('gm convert "%s" -resize 600 "%s"' % (filename, f))


def crumbify(path):
    if path == '.':
        return BREAD_HERO
    breadcrumbs = BREAD
    crumbs = '/'
    for crumb in path.split('/')[1:]:
        crumbs += crumb + '/'
        breadcrumbs += CRUMB.format(cpath=crumbs, child=crumb)
    return breadcrumbs


def get_folderdata(path):
    if os.path.exists(os.path.join(path, 'private')):
        return {}
    folderdata = {'child': os.path.split(path)[1]}
    index = os.path.join(path, 'index.dllu')
    if os.path.exists(index):
        content = open(index).read().split('\n===\n', 1)[0]
        content = [d for d in content.split('\n') if d.strip() != '']
        if len(content) >= 1:
            folderdata['title'] = dllup.parsetext(content[0])
        if len(content) >= 2:
            folderdata['subtitle'] = dllup.parsetext(content[1])
    else:
        return {}
    for extension in RASTER_IMG:
        if os.path.exists(path + extension):
            folderdata['pic'] = os.path.split(path)[1] + extension
    if re.match('y\d\d\d\dm\d\dd\d\d', os.path.split(path)[1]):
        folderdata['date'] = re.sub('m|d', '-', os.path.split(path)[1][1:])
    return folderdata


def main():
    global htmlhead, htmlfoot
    htmlhead = open('html/head.html').read()
    htmlfoot = open('html/foot.html').read()
    cssname = 'dllu-%s.css' % hashlib.sha1(
        struct.pack('f', os.path.getmtime('css'))).hexdigest()
    os.system('sassc -t compressed css/dllu.scss > %s' % cssname)
    htmlhead = htmlhead.replace('dllu.css', cssname)
    recurse('.')


if __name__ == '__main__':
    main()
