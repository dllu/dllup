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

import html
import re
import hashlib
import urllib.request
import urllib.parse
import os
import sys

import pygments
import pygments.lexers
import pygments.formatters

def splitparse(s, delim, yes, no):
    return ''.join([yes(ss) if i%2 == 1 else no(ss) for (i,ss) in enumerate(re.split('(?<!\\\\)'+delim, s))])

def escape(s):
    latextable = {
            '&':r'\&',
            '%':r'\%',
            '#':r'\#',
            '_':r'\_'
    }
    for k in latextable:
        s = s.replace(k, latextable[k])
    return s

def parse(s):
    s = s.replace('\r', '')
    global hnum
    global fignum
    global tablenum
    global eqnum
    global toc
    hnum = [0]*6
    fignum = 0
    tablenum = 0
    eqnum = 0
    ss = s.split('\n===\n', 1)
    if len(ss) > 1:
        header = parseheader(ss[0])
        body = parseraw(ss[1])
        return '\\title{%s}\n\\maketitle\n%s' % (header, body)
    body = parseraw(s)
    return body

def parseheader(s):
    return s.strip().replace('\n\n','\n').replace('\n', '\\\\')

def parseraw(s):
    return splitparse(s, '\n\\?\\?\\?\n', lambda x: '%s' % x, parsecode)

def parsecode(s):
    return splitparse(s, '\n~~~\n', highlight, parsecode2)

def parsecode2(s):
    return splitparse(s, '\n~~~~\n', lambda x: '\\begin{lstlisting}\n%s\n\\end{lstlisting}\n' % x, parsenormal)

def parsenormal(s):
    return ''.join(parseblock(ss) for ss in s.strip().split('\n\n'))

def parseblock(s):
    global hnum
    global eqnum
    global toc
    if len(s.split()) == 0: 
        return ''
    for h in range(3,0,-1):
        # header
        if s[:h] == '#'*h:
            hnum[h-1] += 1
            for j in range(h,6):
                if hnum[j] > 0:
                    hnum[j] = 0
            hh = '.'.join([str(jj) for jj in hnum[:h]])
            hhh = parsetext(s[h:])
            return '\\%ssection{%s}\n\\label{s%s}\n' % ('sub'*(h-1), hhh, hh)
    if s[:2] == '> ':
        # blockquote
        return '\\begin{quote}\n%s\\end{quote}\n' % parsetext(s[2:])
    if s[:4] == 'pic ':
        # images
        return parsepics(s)
    if s[:2] == '$ ':
        # equation
        eqnum += 1
        return '\\begin{align}\n\\label{eq%d}\n%s\\end{align}\n' % (eqnum, parsemath(s[2:]))
    if s[:4] == '* [#':
        # bibliography
        return parsebib(s)
    if s[:2] == '* ':
        # list
        return parseul(s, 1)
    if s[:3] == '1. ':
        # numbered list
        return '\\begin{enumerate}\n%s\\end{enumerate}\n' % parseol(s)
    if s[:2] == '| ':
        # table
        return parsetable(s)
    if s[:3] == ':: ':
        # big button
        s = s[3:].rsplit(' ', 1)
        return '\\begin{center}\\huge \\href{%s}{%s}\\end{center}\n' % (s[1], s[0])
    return '\\par %s\n' % (parsetext(s))

def parsepics(s):
    global fignum
    lines = [ss[4:].split(None, 1) for ss in s.split('\n')]
    out = ''
    for ss in lines:
        fignum += 1
        ss[1] = ss[1].split(': ', 1)
        pic = ss[0]
        if pic[:4]=='http':
            if not os.path.isfile(pic.split('/')[-1]):
                os.system('wget %s' % pic)
            pic = pic.split('/')[-1]
        if pic[-4:] == '.svg':
            pic = pic[:-4] + '.pdf'
        t = (pic, parsetext(ss[1][1]), fignum)
        out += '\\begin{figure}[!htb]\n\\centering\n\\includegraphics[width=0.8\\textwidth]{%s}\n\\caption{\\small %s}\n\\label{fig%d}\n\\end{figure}\n' % t
    return out

def parseul(s, level):
    s = '\n'+s
    items = [ss.strip() for ss in ('\n' + s).split('\n' + '*'*level + ' ')]
    out = parsetext(items[0])
    if len(items) > 1:
        out += '\\begin{itemize}%s\\end{itemize}\n' % ''.join(['\\item %s\n' % parseul(item, level+1) for item in items[1:]])
    return out

def parsebib(s):
    return '\\begin{thebibliography}{99}\n%s\n\\end{thebibliography}' % '\n'.join(parsetext('[#'+ss.split('[#')[1]) for ss in s.split('\n*'))

def parseol(s):
    return ''.join(['\item %s\n' % parsetext(ss) for ss in re.split('\n\\d+\\. ', s[2:])])

def parsetable(s):
    global tablenum
    tablenum += 1
    rows = s.split('\n')
    th = parseth(rows[0])
    trows = ''.join([parserow(row) for row in rows[1:-1]])
    ccc = 'c'*(len(rows[0]))
    table = (ccc, th, trows, parsetext(rows[-1]), tablenum)
    return '\\begin{table}[h]\n\\centering\n\\begin{tabular}{%s}\n%s%s\\end{tabular}\n\\caption{%s}\n\\label{table%d}\\end{table}' % table

def parseth(s):
    return '%s\\\\ \\hline\n' % ' & '.join(['%s' % parsetext(th) for th in s.split('|') if th.strip() is not ''])

def parserow(s):
    if re.match('^(\\||\\s|\\-)*$', s) is not None:
        return ''
    return '%s\\\\\n' % ' & '.join(['%s' % parsetext(td) for td in s.split('|') if td.strip() is not ''])

def parsetext(s):
    return splitparse(s.strip(), '`', lambda x: '\\texttt{%s}' % escape(x), parsetext2)

def parsetext2(s):
    return splitparse(s, '\\$', lambda x: '$%s$' % parsemath(x), parselink)

def parselink(s):
    return parseref(re.sub('\\[([^\\]]+)\\]\\(([^)]+)\\)', '\n~~~\n\\href{\\2}{\n~~~\n\\1\n~~~\n}\n~~~\n', s))

def parseref(s):
    return parsecite(re.sub('\\[\\#([^\\]]+)\\]', '\n~~~\n\\\\bibitem{\\1}\n~~~\n', s))

def parsecite(s):
    s = re.sub('\\(\\#([a-z]+)([0-9\\.]+)\\)', '\n~~~\n\\1~\\\\ref{\\1\\2}\n~~~\n', s)
    s = re.sub('\\(\\#([^\\)]+)\\)', '\n~~~\n\\\\cite{\\1}\n~~~\n', s)
    return parsespan(s)

def parsespan(s):
    return splitparse(s, '\n~~~\n', lambda x: x, parseem)

def parseem(s):
    return splitparse(s, '_', lambda x: '\\emph{%s}' % typographer(x), parsestrong)

def parsestrong(s):
    return splitparse(s, '\\*\\*', lambda x: '\\textbf{%s}' % typographer(x), typographer) 

def typographer(s):
    s = re.sub('"(\\w)', '``\\1', s)
    s = re.sub('(\\s)"', '\\1``', s)
    s = re.sub("(?<!\\w)'(\\w)", '`\\1', s)
    s = re.sub("(\\s)'", '\\1`', s)
    return escape(s.replace('"', "''"))

def parsemath(s):
    return s

def highlight(s):
    firstline = s.split('\n',1)[0]
    output = '\\begin{lstlisting}'
    if firstline[:5] == 'lang ':
        output += '[language='+firstline[5:]+']'
        s = s.split('\n',1)[1]
    return output + '\n' + s + '\n\\end{lstlisting}\n'

def main():
    s = ''
    while True:
        try:
            s += input() + '\n'
        except EOFError:
            break
    print('% LaTeX document generated using dllup. www.dllu.net/programming/dllup/')
    print(parse(s))

if __name__ == '__main__':
    main()
