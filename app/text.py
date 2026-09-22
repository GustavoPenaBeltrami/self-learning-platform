"""HTML <-> Markdown conversion for the subset the editor uses.

Blocks:   h1-h6, p, ul/li, and raw HTML on its own line (cards, figures).
Inline:   strong/b -> **, em/i -> *, s/del -> ~~, a.ref -> [[x]].
Raw:      mark, u, span, aside, figure, img are kept as HTML inside the .md.
          Markdown accepts inline HTML, so the file still opens fine
          in Obsidian and keeps colors, comments and positions.

Self-check: python3 app/text.py
"""
import re
import unicodedata
from html import escape as _escape, unescape as _unescape
from html.parser import HTMLParser

RAW = {"mark", "u", "span", "aside", "figure", "figcaption", "img", "br"}
VOID = {"br", "img", "hr"}
INLINE = {"strong": "**", "b": "**", "em": "*", "i": "*",
          "s": "~~", "del": "~~", "strike": "~~"}
BLOCK = {"p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"}

VIZ = {"mermaid", "math"}
_FIGURE = re.compile(r"<figure\b([^>]*)>\s*<pre\b[^>]*>(.*?)</pre>.*?</figure>", re.S)
_KIND = re.compile(r'data-kind="([a-z]+)"')
_OPEN_FENCE = re.compile(r"^```([a-z]+)\s*$")


def _figure(kind, source):
    """Atomic block: the <pre> is the source, viz.js paints the <div>."""
    return (f'<figure class="viz" data-kind="{kind}" contenteditable="false">'
            f'<pre class="src">{_escape(source, quote=False)}</pre>'
            f'<div class="view"></div></figure>')


def slug(text, default="section"):
    t = unicodedata.normalize("NFD", text)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t)).strip("-") or default


def _open(tag, attrs):
    return "<" + tag + "".join(f' {k}="{v}"' for k, v in attrs if v is not None) + ">"


class _ToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.raw = 0        # depth inside an element that is copied as is
        self.ref = None     # text accumulated from an <a class="ref">
        self.inblock = 0    # inside a p/h/li: an image there goes inline
        self.lists = []

    def handle_starttag(self, tag, attrs):
        if self.raw:
            self.parts.append(_open(tag, attrs))
            if tag not in VOID:
                self.raw += 1
            return
        if tag in RAW:
            if tag in ("aside", "figure") or (tag == "img" and not self.inblock):
                self.parts.append("\n\n")      # own block, own line
            self.parts.append(_open(tag, attrs))
            if tag not in VOID:
                self.raw = 1
            return
        classes = dict(attrs).get("class", "")
        if tag == "a" and "ref" in classes:
            self.ref = ""
            return
        if tag in INLINE:
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

    def handle_startendtag(self, tag, attrs):
        self.parts.append(_open(tag, attrs)) if (self.raw or tag in RAW) \
            else self.parts.append("\n" if tag == "br" else "")

    def handle_endtag(self, tag):
        if self.raw:
            self.parts.append(f"</{tag}>")
            self.raw -= 1
            if self.raw == 0 and tag in ("aside", "figure"):
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
            self.parts.append("\n")

    def handle_data(self, data):
        if self.raw:
            self.parts.append(data)
        elif self.ref is not None:
            self.ref += data
        elif data.strip() == "" and "\n" in data:
            pass          # break between blocks of our own HTML, not text
        else:
            self.parts.append(data.replace("\n", " "))


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
                  lambda m: f'<a class="ref" href="#{slug(m.group(1))}">{m.group(1)}</a>', line)
    line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
    line = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", line)
    line = re.sub(r"~~(.+?)~~", r"<s>\1</s>", line)
    return line


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
        if opens and opens.group(1) in VIZ:
            close()
            body = []
            while i < len(lines) and lines[i].strip() != "```":
                body.append(lines[i])
                i += 1
            i += 1
            out.append(_figure(opens.group(1), "\n".join(body).strip("\n")))
            continue
        if not raw.strip():
            close()
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
    return "\n".join(out)


def split_by_h1(html):
    """[(title, html)] per h1. Whatever comes before the first h1 goes separately."""
    chunks = re.split(r"(?=<h1[ >])", html)
    sections = []
    for t in chunks:
        if not t.strip():
            continue
        m = re.match(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else "Untitled"
        sections.append((title, t))
    return sections


if __name__ == "__main__":
    h = ('<h1>Fundamentals</h1><p>Text with <b>bold</b> and <i>italic</i> and <s>struck</s>.</p>'
         '<h2>Coupling</h2><ul><li>One</li><li>Two</li></ul>'
         '<p>See <a class="ref" href="#styles">Styles</a> too.</p>'
         '<p>A <mark class="mk mk-bg" style="--c: #D9C46A" title="careful">highlight</mark> here.</p>')
    md = html_to_md(h)
    assert "# Fundamentals" in md, md
    assert "## Coupling" in md, md
    assert "**bold**" in md and "*italic*" in md and "~~struck~~" in md, md
    assert "- One\n- Two" in md, md
    assert "[[Styles]]" in md, md
    assert '<mark class="mk mk-bg" style="--c: #D9C46A" title="careful">highlight</mark>' in md, md

    back = md_to_html(md)
    assert "<h1>Fundamentals</h1>" in back, back
    assert "<b>bold</b>" in back and "<i>italic</i>" in back, back
    assert "<li>One</li>" in back and "<ul>" in back, back
    assert '<a class="ref" href="#styles">Styles</a>' in back, back
    assert "<mark" in back and 'title="careful"' in back, back

    # stable round trip: converting twice changes nothing
    assert html_to_md(back) == md, html_to_md(back) + "\n---\n" + md

    sections = split_by_h1(back)
    assert len(sections) == 1 and sections[0][0] == "Fundamentals", sections

    # a blank line is intentional: it survives as a raw <br>
    for given in ('<p>one</p><p><br></p><p>two</p>',
                  '<h2>T</h2><div><br></div><p>x</p>',
                  '<p>a</p><div></div><p>b</p>',
                  '<p>one<br>two</p>'):
        md1 = html_to_md(given)
        assert "<br>" in md1, (given, md1)
        assert html_to_md(md_to_html(md1)) == md1, (md1, html_to_md(md_to_html(md1)))

    # drawings: the fence is the source of truth and survives the round trip
    md_viz = ("# Ch\n\ntext\n\n```mermaid\ngraph TD\n  A[Package] --> B{Order}\n"
              "```\n\nmore text\n\n```math\np_{99} = \\frac{x}{y}\n```\n")
    h_viz = md_to_html(md_viz)
    assert '<figure class="viz" data-kind="mermaid"' in h_viz, h_viz
    assert "A[Package] --&gt; B{Order}" in h_viz, h_viz
    assert '<figure class="viz" data-kind="math"' in h_viz, h_viz
    assert html_to_md(h_viz) == md_viz, html_to_md(h_viz)

    # whatever the browser paints inside the figure is dropped on save
    painted = h_viz.replace('<div class="view"></div>',
                            '<div class="view"><svg><g>junk</g></svg></div>', 1)
    assert html_to_md(painted) == md_viz, html_to_md(painted)

    # a figure that isn't a drawing is still copied as is
    other = '<figure><img src="x.png"><figcaption>caption</figcaption></figure>'
    assert "<figcaption>caption</figcaption>" in html_to_md(other), html_to_md(other)

    # a fence right after a list closes the list, doesn't swallow it
    md_list = "- one\n- two\n\n```mermaid\ngraph LR\n  A --> B\n```\n"
    assert md_to_html(md_list).count("</ul>") == 1, md_to_html(md_list)
    assert html_to_md(md_to_html(md_list)) == md_list, html_to_md(md_to_html(md_list))

    md_num = "1. one\n2. two\n\n- a\n- b\n"
    h_num = md_to_html(md_num)
    assert "<ol>" in h_num and "<ul>" in h_num, h_num
    assert html_to_md(h_num) == md_num, html_to_md(h_num)

    two = split_by_h1("<h1>One</h1><p>a</p><h1>Two</h1><p>b</p>")
    assert [t for t, _ in two] == ["One", "Two"], two
    assert slug("Cap 1 — Introducción") == "cap-1-introduccion"
    print("text.py ok")
