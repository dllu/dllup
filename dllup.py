#!/usr/bin/env python3
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
import os
import sys
import subprocess

import pygments
import pygments.lexers
import pygments.formatters


def splitparse(s, delim, yes, no):
    return "".join(
        [
            yes(ss) if i % 2 == 1 else no(ss)
            for (i, ss) in enumerate(re.split("(?<!\\\\)" + delim, s))
        ]
    )


def unescape(s):
    return re.sub("(?<!\\\\)\\\\", "", s)


def parse(s):
    s = s.replace("\r", "")
    global hnum
    global fignum
    global tablenum
    global eqnum
    global toc
    global metas
    hnum = [0] * 6
    fignum = 0
    tablenum = 0
    eqnum = 0
    toc = ""
    metas = {}
    ss = s.split("\n===\n", 1)
    if len(ss) > 1:
        header = parseheader(ss[0])
        body = parseraw(ss[1])
        toc += "".join(["</ol>" for hh in hnum if hh > 0])
        return f'<header>{header}<div class="toc">{toc}</div></header>{body}', metas
    body = parseraw(s)
    if toc != "":
        return f'<header><div class="toc">{toc}</div></header>{body}'
    return body, metas


def parseheader(s):
    s = s.strip().split("\n\n")
    return '<h1 id="top">{}</h1>{}'.format(
        parsetext(s[0]),
        "".join(["<p>%s</p>" % parsetext(ss) for ss in s[1:]]),
    )


def parseraw(s):
    return splitparse(s, "\n\\?\\?\\?\n", lambda x: "%s" % x, parsecode)


def parsecode(s):
    return splitparse(s, "\n~~~\n", highlight, parsecode2)


def parsecode2(s):
    return splitparse(
        s, "\n~~~~\n", lambda x: "<pre>%s</pre>" % html.escape(x), parsenormal
    )


def parsenormal(s):
    return "".join(parseblock(ss) for ss in s.strip().split("\n\n"))


def parseblock(s):
    global hnum
    global eqnum
    global toc
    if len(s.split()) == 0:
        return ""
    for h in range(6, 0, -1):
        # header
        if s[:h] == "#" * h:
            if hnum[h - 1] == 0:
                toc += "<ol>"
            hnum[h - 1] += 1
            for j in range(h, 6):
                if hnum[j] > 0:
                    toc += "</ol></li>"
                    hnum[j] = 0
            if hnum[h] > 0:
                toc += "</li>"
            hh = ".".join([str(jj) for jj in hnum[:h]])
            hhh = parsetext(s[h:])
            toc += (
                '<li><a href="#s%s"><span class="tocnum">%s</span> <span>%s</span></a>'
                % (hh, hh, hhh)
            )
            return (
                '<h%d id="s%s"><a href="#s%s" class="hnum">%s</a> <span>%s</span></h%d>'
                % (h, hh, hh, hh, hhh, h)
            )
    if s[:2] == "> ":
        # blockquote
        return "<blockquote>%s</blockquote>" % parsetext(s[2:])
    if s[:4] == "pic ":
        # images
        return '<div class="pics">%s</div>' % parsepics(s)
    if s[:2] == "$ ":
        # equation
        eqnum += 1
        return (
            '<div class="math" id="eq%d"><a href="#eq%d" class="eqnum">%d</a> %s</div>'
            % (eqnum, eqnum, eqnum, parsemath("%s" % s[2:]))
        )
    if s[:2] == "* ":
        # list
        return parseul(s, 1)
    if s[:3] == "1. ":
        # numbered list
        return "<ol>%s</ol>" % parseol(s)
    if s[:2] == "| ":
        # table
        return parsetable(s)
    if s[:3] == ":: ":
        # big button
        s = s[3:].rsplit(" ", 1)
        return '<p><a href="{}" class="bigbutton">{}</a></p>'.format(s[1], s[0])

    if "description" not in metas:
        metas["description"] = first_sentence(s)
    return "<p>%s</p>" % (parsetext(s))


def first_sentence(s):
    s = " ".join(s.split("\n"))
    return s.split(". ")[0] + "."


def parsepics(s):
    global fignum
    global metas
    lines = [ss[4:].split(None, 1) for ss in s.split("\n")]
    out = ""
    for ss in lines:
        fignum += 1
        ss[1] = ss[1].split(": ", 1)
        # use an image that is resized to 600px instead if the image is locally referenced
        pic = ss[0]
        ss[1][1] = ss[1][1].split(" (full size: ")
        fullpic = ss[0]
        if (
            len(ss[1][1]) == 1
            and ss[0][:4] != "http"
            and ss[0][-4:] in [".png", ".jpg"]
        ):
            pic = ss[0][:-4] + "_600" + ss[0][-4:]
        elif len(ss[1][1]) == 2:
            # if the description contains the string " (full size: %s)" then use that
            fullpic = ss[1][1][1][:-1]
        out += f'<figure id="fig{fignum}"><a href="{fullpic}"><img src="{pic}" alt="{ss[1][0]}"/></a><figcaption><a href="#fig{fignum}" class="fignum">FIGURE {fignum}</a> {parsetext(ss[1][1][0])}</figcaption></figure>'

        if "image" not in metas:
            metas["image"] = pic

    return out


def parseul(s, level):
    s = "\n" + s
    items = [ss.strip() for ss in ("\n" + s).split("\n" + "*" * level + " ")]
    out = parsetext(items[0])
    if len(items) > 1:
        out += "<ul>%s</ul>" % "".join(
            ["<li>%s</li>" % parseul(item, level + 1) for item in items[1:]]
        )
    return out


def parseol(s):
    return "".join(
        ["<li>%s</li>" % parsetext(ss) for ss in re.split("\n\\d+\\. ", s[2:])]
    )


def parsetable(s):
    global tablenum
    tablenum += 1
    rows = s.split("\n")
    table = (
        tablenum,
        parseth(rows[0]),
        "".join([parserow(row) for row in rows[1:-1]]),
        tablenum,
        tablenum,
        parsetext(rows[-1]),
    )
    return (
        '<figure id="table%d"><table>%s%s</table><figcaption><a href="#table%d" class="fignum">Table %d</a> %s</figcaption></figure>'
        % table
    )


def parseth(s):
    return "<tr>%s</tr>" % "".join(
        ["<th>%s</th>" % parsetext(th) for th in s.split("|") if th.strip() != ""]
    )


def parserow(s):
    if re.match("^(\\||\\s|\\-)*$", s) is not None:
        return ""
    return "<tr>%s</tr>" % "".join(
        ["<td>%s</td>" % parsetext(td) for td in s.split("|") if td.strip() != ""]
    )


def parsetext(s):
    return splitparse(
        s.strip(), "`", lambda x: "<code>%s</code>" % html.escape(x), parsetext2
    )


def parsetext2(s):
    return splitparse(s, "\\$", lambda x: "%s" % parsemath(x, True), parselink)


def parselink(s):
    return parseref(
        re.sub(
            "\\[([^\\]]+)\\]\\(([^)]+)\\)",
            '\n~~~\n<a href="\\2">\n~~~\n\\1\n~~~\n</a>\n~~~\n',
            s,
        )
    )


def parseref(s):
    return parsecite(
        re.sub(
            "\\[\\#([^\\]]+)\\]",
            '\n~~~\n<span class="refname" id="\\1">\\1</span>\n~~~\n',
            s,
        )
    )


def parsecite(s):
    return parsespan(
        re.sub(
            "\\(\\#([^\\)]+)\\)",
            '\n~~~\n<a class="refname" href="#\\1">\\1</a>\n~~~\n',
            s,
        )
    )


def parsespan(s):
    return splitparse(s, "\n~~~\n", lambda x: x, parseem)


def parseem(s):
    return splitparse(s, "_", lambda x: "<em>%s</em>" % typographer(x), parsestrong)


def parsestrong(s):
    return splitparse(
        s, "\\*\\*", lambda x: "<strong>%s</strong>" % typographer(x), typographer
    )


def typographer(s):
    s = re.sub('"(\\w)', "“\\1", s)
    s = re.sub('(\\s)"', "\\1“", s)
    s = re.sub("(?<!\\w)'(\\w)", "‘\\1", s)
    s = re.sub("(\\s)'", "\\1‘", s)
    return html.escape(
        unescape(
            s.replace("---", "—")
            .replace("--", "–")
            .replace('"', "”")
            .replace("'", "’")
            .replace("...", "…")
        )
    )


greekbm = re.compile(
    r"\\bm ?\\(0|1|alpha|beta|gamma|delta|epsilon|lambda|mu|nu|sigma|xi|zeta|omega|eta|theta|kappa|omicron|pi|rho|tau|upsilon|phi|psi|chi|Alpha|Beta|Gamma|Delta|Epsilon|Lambda|Mu|Nu|Sigma|Xi|Zeta|Omega|Eta|Theta|Kappa|Omicron|Pi|Rho|Tau|Upsilon|Phi|Psi|Chi)"
)


def parsemath(s, inline=False):
    shash = hashlib.sha1(s.encode("utf-8")).hexdigest()
    if inline:
        shash += "i"
    elif "\\begin{align}" not in s:
        s = "\\displaystyle{\\begin{align}" + s + "\\end{align}}"
    filename = shash + ".svg"
    filepath = os.path.join("texcache", filename)

    s = re.sub(greekbm, r"\\boldsymbol{\\\1}", s)
    try:
        if not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
            # extra space so that it won't be treated as an option if starting with '-'
            mathjaxargs = ["tex2svg", " " + s]
            if inline:
                mathjaxargs.append("--inline")
            p = subprocess.Popen(mathjaxargs, stdout=subprocess.PIPE)
            jax, errors = p.communicate()
            if errors:
                sys.stderr.write("Equation error: {}\n", errors)
            else:
                f = open(filepath, "w")
                f.write(jax.decode("utf-8"))
                f.close()
        jax = open(filepath).read()
        style = re.search('style=".*?"', jax)
        height = re.search('height=".*?"', jax)
        height = jax[height.start() : height.end()]
        height = height.replace("=", ":").replace('"', "")
        style = jax[style.start() : style.end() - 1] + height + ';"'
        return '<img src="/texcache/{}" alt="{}" {}/>'.format(
            filename,
            html.escape(s),
            style,
        )
    except Exception as e:
        sys.stderr.write(f"Equation error: {s}\n{e}\n")
        return ""


def highlight(s):
    firstline = s.split("\n", 1)[0]
    if firstline[:5] == "lang ":
        lexer = pygments.lexers.get_lexer_by_name(firstline[5:], stripall=True)
        s = s.split("\n", 1)[1]
    else:
        lexer = None
        try:
            lexer = pygments.lexers.guess_lexer(s)
        except pygments.util.ClassNotFound:
            lexer = pygments.lexers.special.TextLexer
    return pygments.highlight(s, lexer, pygments.formatters.HtmlFormatter())


def main():
    s = ""
    while True:
        try:
            s += input() + "\n"
        except EOFError:
            break
    print(parse(s))


if __name__ == "__main__":
    main()
