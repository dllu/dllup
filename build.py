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
from get_image_dimensions import get_image_dimensions
import hashlib
import os
import re
import struct
import time
import PIL
from pathlib import Path
from operator import itemgetter

RASTER_IMG = [".png", ".jpg"]
# navigation markup
PORTFOLIO_NAV = '<a href="{child}"><figure><img src="{pic}" alt="{child_name}"/><figcaption>{title} ({subtitle})</figcaption></figure></a>'
BLOG_NAV = '<a href="{child}"><span class="blogdate">{date}</span><span class="blogtitle">{title}</span></a>'
ROOT_NAV = '<a href="{child}">{child_name}</a>'
# the first breadcrumb
BREAD = '<a href="/"><span id="dllu"><span style="display:none;">dllu</span><span id="D"></span><span id="L0"></span><span id="L1"></span><span id="U"></span></span></a><span>/</span>'
BREAD_HERO = '<a href="/" id="hero-a"><span id="dllu-hero"><span style="display:none;">dllu</span><span id="D"></span><span id="L0"></span><span id="L1"></span><span id="U"></span></span></a>'
# all consecutive breadcrumbs
CRUMB = '<a href="{cpath}">{child}</a><span>/</span>'

# page markup
PAGE = '<!DOCTYPE html>\n{sig}\n{htmlhead}<nav id="breadcrumbs">{breadcrumbs}</nav><nav id="rootnav">{rootnav}</nav><nav id="{navtype}">{nav}</nav><main>{output}<footer><p>&copy; Daniel Lawrence Lu. Page generated on {time} by <a href="/programming/dllup/">dllup</a>. (<a href="{text}">text version</a>)</footer></main>{htmlfoot}'
PAGE_HERO = PAGE.replace('id="breadcrumbs"', 'id="hero"')


def readconfig(configpath: Path):
    # Reads a config file which is a simple text file of key-value pairs.
    # One key-value pair per line, key (no whitespaces) is separated from
    # value by whitespace.
    # Valid keys are: type, root
    if not configpath.exists():
        return {}
    config = open(configpath).read()
    configsplit = [cc.split(None, 1) for cc in config.split("\n")]
    return {c[0]: c[1] for c in configsplit if len(c) >= 2}


def recurse(path: Path = Path(), rootnav="", root=""):
    global htmlhead
    global htmlfoot
    children = list(path.iterdir())
    folderdata = [get_folderdata(c) for c in children if c.is_dir()]

    config = readconfig(path / "config")
    if "root" in config:
        root = config["root"]
    navtype = config["type"] if "type" in config else None

    # generate navigation markup
    nav = ""
    if navtype == "blogposts":
        folderdata = sorted(
            [f for f in folderdata if "date" in f],
            key=itemgetter("date"),
            reverse=True,
        )
    elif navtype == "portfolio":
        folderdata = sorted(
            [f for f in folderdata if "subtitle" in f],
            key=itemgetter("subtitle"),
            reverse=True,
        )
    else:
        folderdata = sorted(
            [f for f in folderdata if "child" in f], key=itemgetter("child")
        )
    for f in folderdata:
        try:
            f["child"] = f'{root}/{f["child"]}'
            if navtype == "root":
                rootnav += ROOT_NAV.format(**f)
            elif navtype == "blogposts":
                nav += BLOG_NAV.format(**f)
            elif navtype == "portfolio":
                nav += PORTFOLIO_NAV.format(**f)
        except KeyError:
            pass  # ignore folders without complete data

    breadcrumbs = generate_breadcrumbs(path, root)
    # recurse through children
    for child in children:
        if child.is_dir():
            recurse(child, rootnav, root)
        if child.suffix in RASTER_IMG and "_600" not in child.name:
            resize_images(path, child)
            pass
        elif child.suffix == ".dllu":
            with open(child) as o:
                markup = o.read()
            hash = hashlib.sha1(
                struct.pack("f", child.stat().st_mtime) + b"dllu"
            ).hexdigest()
            sig = f"<!--{hash}-->"
            sig2 = None
            try:
                with open(path / (child.stem + ".html")) as f:
                    f.readline()
                    sig2 = f.readline()
            except FileNotFoundError:
                pass
            if sig == sig2:
                continue

            output, metas = dllup.parse(markup)
            PP = PAGE
            if path == Path():
                PP = PAGE_HERO

            ss = markup.split("\n===\n", 1)
            if len(ss) > 1:
                title = ss[0].strip()
            else:
                title = child.parent.name

            metas["title"] = title
            if "image" in metas:
                width, height = None, None
                if metas["image"][:7] != "http://" and metas["image"][:8] != "https://":
                    try:
                        width, height = get_image_dimensions(
                            str(path / metas["image"]), "img_size_db.db"
                        )
                    except PIL.UnidentifiedImageError:
                        pass
                    metas["image"] = f'{root}/{path}/{metas["image"]}'
                else:
                    try:
                        width, height = get_image_dimensions(metas["image"])
                    except PIL.UnidentifiedImageError:
                        pass
                if width is not None and height is not None:
                    metas["image:width"] = width
                    metas["image:height"] = height

            meta_html = format_meta(metas)
            head = htmlhead.format(title=title, metas=meta_html)

            with open(path / (child.stem + ".html"), "w") as f:
                f.write(
                    PP.format(
                        htmlhead=head,
                        htmlfoot=htmlfoot,
                        breadcrumbs=breadcrumbs,
                        rootnav=rootnav,
                        navtype=navtype,
                        output=output,
                        time=time.strftime("%Y-%m-%d", time.gmtime()),
                        child=child,
                        nav=nav,
                        sig=sig,
                        text=child,
                    )
                    .replace(
                        ' src="/',
                        f' src="{root}/',
                    )
                    .replace(
                        ' href="/',
                        f' href="{root}/',
                    )
                )


def format_meta(metas):
    meta_html = "\n".join(
        f'<meta property="og:{k}" content="{v}" />' for k, v in metas.items()
    )
    if "image" in metas:
        meta_html += '<meta name="twitter:card" content="summary_large_image">'
    if "description" in metas:
        meta_html += f'<meta name="description" content="{metas["description"]}" />'
    meta_html += '<meta name="robots" content="max-image-preview:large">'
    return meta_html


def resize_images(path, child):
    filename = path / child
    filename600 = path / (filename.stem + "_600" + filename.suffix)
    filename600x2 = path / (filename.stem + "_600@2x" + filename.suffix)
    for f in (filename600, filename600x2):
        scale = 600
        if "@2x" in f.stem:
            scale = 1200
        if not f.exists():
            os.system(f'gm convert "{filename}" -resize {scale} "{f}"')


def generate_breadcrumbs(path, root):
    if path == Path():
        return BREAD_HERO
    breadcrumbs = BREAD
    cpath = Path()
    for crumb in path.parts:
        cpath = cpath / crumb
        breadcrumbs += CRUMB.format(cpath=f"{root}/{cpath}", child=crumb)
    return breadcrumbs


def get_folderdata(path):
    if (path / "private").exists():
        return {}

    folderdata = {"child": path}
    index = path / "index.dllu"
    if index.exists():
        content = open(index).read().split("\n===\n", 1)[0]
        content = [d for d in content.split("\n") if d.strip() != ""]
        if len(content) >= 1:
            folderdata["title"] = dllup.parsetext(content[0])
        if len(content) >= 2:
            folderdata["subtitle"] = dllup.parsetext(content[1])
    else:
        return {}
    for extension in RASTER_IMG:
        if (path.parent / (path.name + extension)).exists():
            folderdata["pic"] = path.name + extension
    if re.match(r"y\d\d\d\dm\d\dd\d\d", path.name):
        folderdata["date"] = re.sub("m|d", "-", path.name[1:])

    folderdata["child_name"] = path.name

    return folderdata


def main():
    global htmlhead, htmlfoot
    with open("html/head.html") as f:
        htmlhead = f.read()
    with open("html/foot.html") as f:
        htmlfoot = f.read()
    hash = hashlib.sha1(struct.pack("f", os.path.getmtime("css"))).hexdigest()
    cssname = f"dllu-{hash}.css"
    os.system(f"sassc -t compressed css/dllu.scss > {cssname}")
    htmlhead = htmlhead.replace("dllu.css", cssname)
    recurse()


if __name__ == "__main__":
    main()
