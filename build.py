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

import os
import uuid
import dllup
import time
import re

# ROOT = 'http://frc.ri.cmu.edu/~daniellu'
# ROOT = 'http://www.dllu.net'
ROOT = 'http://daniel.lawrence.lu'
# ROOT = ''

# compile the CSS with a random name
# os.system('rm site/*.css')
cssname = 'dllu-%s.css' % str(uuid.uuid4())
os.system('scss css/dllu.scss > site/%s' % cssname) # load the head and foot of the html template
htmlhead = open('html/head.html').read()
htmlfoot = open('html/foot.html').read()

htmlhead = htmlhead.replace('dllu.css', cssname)

# recursively dllup compile all the .dllu files
def recurse(path, rootnav=''):
    children = sorted(os.listdir(path))
    navtype = 'descendants'
    if path == 'site/blog':
        children = sorted(children, reverse=True)
        navtype = 'blogposts'
    elif path == 'site/design' or path == 'site/engineering' or path == 'site/programming' or path == 'site/photos':
        navtype = 'portfolio'
    elif path == 'site':
        navtype = 'rootnav'
    nav = ''
    childdata = []
    for child in children:
        if child[-4:] in ['.jpg', '.png'] and not '_600' in child:
            if not os.path.exists(os.path.join(path, child[:-4] + '_600' + child[-4:])):
                filename = os.path.join(path, child)
                filename2 = os.path.join(path, child[:-4] + '_600' + child[-4:])
                os.system('gm convert "%s" -resize 600 "%s"' % (filename, filename2))
            if not os.path.exists(os.path.join(path, child[:-4] + '_600@2x' + child[-4:])):
                filename = os.path.join(path, child)
                filename2 = os.path.join(path, child[:-4] + '_600@2x' + child[-4:])
                os.system('gm convert "%s" -resize 1200 "%s"' % (filename, filename2))
    if navtype == 'portfolio':
        for child in children:
            if os.path.isdir(os.path.join(path, child)):
                pic = ''
                for extension in ['.jpg', '.png']:
                    if os.path.exists(os.path.join(path, child + extension)):
                        pic = child + extension
                filename = os.path.join(path, child, 'index.dllu')
                if os.path.exists(filename):
                    content = open(filename).read().split('\n===\n')[0]
                    content = [d for d in content.split('\n') if d.strip() is not '']
                    if len(content) >= 2:
                        childdata.append((dllup.parsetext(content[1]), dllup.parsetext(content[0]), child, pic))
        for cd in sorted(childdata, reverse=True):
            t = (cd[2], cd[3], cd[2], cd[1], cd[0])
            if not os.path.exists(os.path.join(path, cd[2], 'private')):
                nav += '<a href="%s/"><figure><img src="%s" alt="%s"/><figcaption>%s (%s)</figcaption></figure></a>' % t
    else:
        for child in children:
            if os.path.isdir(os.path.join(path, child)):
                filename = os.path.join(path, child, 'index.dllu')
                if os.path.exists(filename):
                    if path == 'site/blog':
                        t = (child, re.sub('y','', re.sub('m|d', '-', child)), dllup.parsetext(open(filename).read().split('\n')[0]))
                        if not os.path.exists(os.path.join(path, child, 'private')):
                            nav += '<a href="%s/"><span class="blogdate">%s</span><span class="blogtitle">%s</span></a>' % t
                    else:
                        if not os.path.exists(os.path.join(path, child, 'private')):
                            nav += '<a href="%s/">%s</a>' % (os.path.join(path,child)[4:], child)
    if path == 'site':
        rootnav = '<nav id="rootnav">%s</nav>' % nav
    for child in children:
        if os.path.isdir(os.path.join(path, child)):
            recurse(os.path.join(path, child), rootnav)
    breadcrumbs = '<a href="/"><span id="dllu"><span style="display:none;">dllu</span><span id="D"></span><span id="L0"></span><span id="L1"></span><span id="U"></span></span></a><span>/</span>'
    crumbs = '/'
    for crumb in path.split('/')[1:]:
        crumbs += crumb + '/'
        breadcrumbs += '<a href="%s">%s</a><span>/</span>' % (crumbs, crumb)
    if path == 'site':
        rootnav = ''
    for child in children:
        if child[-5:] == '.dllu':
            markup = open(os.path.join(path, child)).read()
            output = dllup.parse(markup)
            f = open(os.path.join(path, child[:-5] + '.html'), 'w')
            f.write(('%s<nav id="breadcrumbs">%s</nav>%s<nav id="%s">%s</nav><article>%s<footer><p>&copy; Daniel Lawrence Lu. Page generated on %s by <a href="/programming/dllup/">dllup</a>. (<a href="%s">text version</a>)</footer></article>%s' % (htmlhead, breadcrumbs, rootnav, navtype, nav, output, time.strftime("%d %b %Y", time.localtime()), child, htmlfoot)).replace(' src="/', ' src="%s/' % ROOT).replace(' href="/', ' href="%s/' % ROOT))
            f.close()

recurse('site')
