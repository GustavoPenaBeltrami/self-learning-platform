"""HTML <-> Markdown conversion for the subset the editor uses.

Blocks:   h1-h6, p, ul/li, GFM pipe tables, and raw HTML on its own line (cards, figures, pre).
Inline:   strong/b -> **, em/i -> *, s/del -> ~~, a.ref -> [[x]].
Raw:      mark, u, span, aside, figure, img, a, code, pre, sub, sup are kept as HTML inside the .md.
          Markdown accepts inline HTML, so the file still opens fine
          in Obsidian and keeps colors, comments and positions.
"""
import re
import unicodedata
from html import escape as _escape, unescape as _unescape
from html.parser import HTMLParser

RAW = {"mark", "u", "span", "aside", "figure", "figcaption", "img", "br", "a", "code", "pre", "sub", "sup"}
OWN_LINE = ("aside", "figure", "pre")
VOID = {"br", "img", "hr", "wbr"}
INLINE = {"strong": "**", "b": "**", "em": "*", "i": "*",
          "s": "~~", "del": "~~", "strike": "~~"}
BLOCK = {"p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"}

VIZ = {"mermaid", "math"}
_FIGURE = re.compile(r"<figure\b([^>]*)>\s*<pre\b[^>]*>(.*?)</pre>.*?</figure>", re.S)
_KIND = re.compile(r'data-kind="([a-z]+)"')
_OPEN_FENCE = re.compile(r"^```([a-z]+)\s*$")
_LEADING = re.compile(r"^(\s*)(#|- |\d+\. |```|\|)")
_DELIM = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")
_DANGER = re.compile(r"<(script|iframe|object|embed)\b.*?</\1\s*>|</?(script|iframe|object|embed)\b[^>]*>", re.I | re.S)
_ON_ATTR = re.compile(r"""\s+on\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", re.I)
_JS_URL = re.compile(r"""((?:href|src)\s*=\s*["']?)\s*javascript:""", re.I)


def _figure(kind, source):
    """Atomic block: the <pre> is the source, viz.js paints the <div>."""
    return (f'<figure class="viz" data-kind="{kind}" contenteditable="false">'
            f'<pre class="src">{_escape(source, quote=False)}</pre>'
            f'<div class="view"></div></figure>')


def slug(text, default="section"):
    t = unicodedata.normalize("NFD", text)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t)).strip("-") or default


def plain(html):
    return _unescape(re.sub(r"<[^>]+>|[*_~`\[\]]", "", html)).strip()


def _esc(s, quote=False):
    s = _escape(s, quote=quote).replace("*", "&#42;")
    return re.sub(r"\[(?=\[)", "&#91;", re.sub(r"~(?=~)", "&#126;", s))


def _open(tag, attrs):
    return "<" + tag + "".join(f' {k}="{_esc(v, True)}"' for k, v in attrs if v is not None) + ">"


class _ToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.raw = 0        # depth inside an element that is copied as is
        self.ref = None     # text accumulated from an <a class="ref">
        self.inblock = 0    # inside a p/h/li: an image there goes inline
        self.lists = []
        self.fresh = True
        self.rows = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if self.raw:
            self.parts.append(_open(tag, attrs))
            if tag not in VOID:
                self.raw += 1
            return
        self.fresh = tag in ("p", "div")
        classes = dict(attrs).get("class") or ""
        if tag == "a" and "ref" in classes.split():
            self.ref = ""
        elif tag in RAW:
            if tag in OWN_LINE or (tag == "img" and not self.inblock):
                self.parts.append("\n\n")
            self.parts.append(_open(tag, attrs))
            if tag not in VOID:
                self.raw = 1
        elif tag in INLINE:
            self.parts.append(INLINE[tag])
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.inblock += 1
            self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
        elif tag == "li":
            self.inblock += 1
            if self.lists and self.lists[-1][0] == "ol":
                self.lists[-1][1] += 1
                self.parts.append(f"\n{self.lists[-1][1]}. ")
            else:
                self.parts.append("\n- ")
        elif tag in ("p", "div"):
            self.inblock += 1
            self.parts.append("\n\n")
        elif tag == "table":
            self.rows = []
        elif tag == "tr" and self.rows is not None:
            self.rows.append([])
        elif tag in ("td", "th") and self.rows:
            self.inblock += 1
            self.cell = len(self.parts)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.raw:
            self.parts.append(f"</{tag}>")
            self.raw -= 1
            if self.raw == 0 and tag in OWN_LINE:
                self.parts.append("\n\n")
            return
        if tag == "a" and self.ref is not None:
            self.parts.append(f"[[{self.ref.strip()}]]")
            self.ref = None
        elif tag in INLINE:
            self.parts.append(INLINE[tag])
        elif tag == "li":
            self.inblock = max(0, self.inblock - 1)   # the next <li> opens its own line
        elif tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
            self.parts.append("\n\n")
        elif tag in BLOCK:
            self.inblock = max(0, self.inblock - 1)
            self.fresh = True
            self.parts.append("\n")
        elif tag in ("td", "th") and self.cell is not None:
            self.inblock = max(0, self.inblock - 1)
            self.rows[-1].append(" ".join("".join(self.parts[self.cell:]).split()).replace("|", "&#124;"))
            del self.parts[self.cell:]
            self.cell = None
        elif tag == "table" and self.rows is not None:
            self.parts.append(_table(self.rows))
            self.rows = None

    def handle_data(self, data):
        if self.raw:
            self.parts.append(_esc(data).replace("\n", "&#10;"))
        elif self.ref is not None:
            self.ref += _esc(data)
        elif data.strip() == "" and "\n" in data:
            pass          # break between blocks of our own HTML, not text
        elif self.rows is not None and self.cell is None:
            pass
        else:
            data = _esc(data.replace("\n", " "))
            if self.fresh:
                data = _LEADING.sub(lambda m: m.group(1) + f"&#{ord(m.group(2)[0])};" + m.group(2)[1:], data)
            self.fresh = False
            self.parts.append(data)


def _table(rows):
    rows = [r for r in rows if r]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    lines = ["| " + " | ".join(r + [""] * (width - len(r))) + " |" for r in rows]
    lines.insert(1, "|" + " --- |" * width)
    return "\n\n" + "\n".join(lines) + "\n\n"


def html_to_md(html):
    # Drawings bypass the parser: they come back as a fence at the end, with
    # their source intact. Whatever the browser painted inside the figure is dropped.
    stash = []

    def _set_aside(m):
        attributes, source = m.group(1), m.group(2)
        if 'class="viz"' not in attributes:
            return m.group(0)
        k = _KIND.search(attributes)
        kind = k.group(1) if k and k.group(1) in VIZ else "mermaid"
        stash.append((kind, _unescape(source)))
        return f"<p>@@VIZ{len(stash) - 1}@@</p>"

    html = _FIGURE.sub(_set_aside, html)
    # An empty block is a blank line the user put there on purpose.
    # Markdown has no way to represent it, so it stays as a raw <br>.
    html = re.sub(r"<(p|div)\b[^>]*>(?:\s|<br\s*/?>|&nbsp;)*</\1>", "<br>", html)
    p = _ToMarkdown()
    p.feed(html)
    p.close()
    md = "".join(p.parts)
    md = re.sub(r"@@VIZ(\d+)@@",
                lambda m: "\n\n```{0}\n{1}\n```\n\n".format(*stash[int(m.group(1))]), md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def _inline(line):
    line = re.sub(r"\[\[([^\]]+)\]\]",
                  lambda m: f'<a class="ref" href="#{slug(_unescape(m.group(1)))}">{m.group(1)}</a>', line)
    line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
    line = re.sub(r"(?<!\*)\*([^\s*](?:[^*]*[^\s*])?)\*(?!\*)", r"<i>\1</i>", line)
    line = re.sub(r"~~(.+?)~~", r"<s>\1</s>", line)
    return line


def _sanitize(html):
    html = _DANGER.sub("", html)
    return re.sub(r"<[^>]+>", lambda m: _JS_URL.sub(r"\1#", _ON_ATTR.sub("", m.group())), html)


def _cells(line):
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def _table_html(rows):
    head = "".join(f"<th>{_inline(c)}</th>" for c in rows[0])
    body = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _fence_end(lines, i):
    for j in range(i, len(lines)):
        if lines[j].strip() == "```":
            return j
    return None


def md_to_html(md):
    out, lst = [], None
    lines = md.split("\n")
    i = 0

    def close():
        nonlocal lst
        if lst:
            out.append(f"</{lst}>")
            lst = None

    def item(kind, text):
        nonlocal lst
        if lst != kind:
            close()
            out.append(f"<{kind}>")
            lst = kind
        out.append(f"<li>{_inline(text)}</li>")

    while i < len(lines):
        raw = lines[i].rstrip()
        i += 1
        opens = _OPEN_FENCE.match(raw.strip())
        end = _fence_end(lines, i) if opens and opens.group(1) in VIZ else None
        if end is not None:
            close()
            out.append(_figure(opens.group(1), "\n".join(lines[i:end]).strip("\n")))
            i = end + 1
            continue
        if not raw.strip():
            close()
            continue
        if raw.strip().startswith("|") and i < len(lines) and _DELIM.match(lines[i].strip()):
            close()
            rows = [_cells(raw)]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            out.append(_table_html(rows))
            continue
        if raw.lstrip().startswith("<"):          # card or figure: as is
            close()
            # a lone <br> is a blank line: empty paragraph, not a loose <br>
            # (loose, it collapses against the neighbor margins and the gap comes out uneven)
            out.append("<p><br></p>" if raw.strip() in ("<br>", "<br/>", "<br />") else raw)
            continue
        head = re.match(r"(#{1,6}) (.*)", raw)
        num = re.match(r"\d+\. (.*)", raw)
        if head:
            close()
            n = len(head.group(1))
            out.append(f"<h{n}>{_inline(head.group(2))}</h{n}>")
        elif raw.startswith("- "):
            item("ul", raw[2:])
        elif num:
            item("ol", num.group(1))
        else:
            close()
            out.append(f"<p>{_inline(raw)}</p>")
    close()
    return _sanitize("\n".join(out))


def split_by_h1(html):
    """[(title, html)] per h1. Whatever comes before the first h1 goes separately."""
    chunks = re.split(r"(?=<h1[ >])", html)
    sections = []
    for t in chunks:
        if not t.strip():
            continue
        m = re.match(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        title = _unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else "Untitled"
        sections.append((title, t))
    return sections
