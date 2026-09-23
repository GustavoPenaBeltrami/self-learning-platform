#!/usr/bin/env python3
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CLASSES = {"mk-fondo": "mk-highlight", "mk-sub": "mk-underline", "mk-tacha": "mk-strike",
           "tarjeta": "card", "cuerpo": "card-body"}


def migrate(md):
    md = re.sub(r'class="([^"]*)"', lambda m: 'class="' + " ".join(CLASSES.get(c, c) for c in m.group(1).split()) + '"', md)
    return re.sub(r"\bdata-nota=", "data-comment=", md)


def run(topics):
    changed = []
    for f in sorted(topics.glob("*/notes/*.md")):
        old = f.read_text(encoding="utf-8")
        new = migrate(old)
        if new != old:
            f.write_text(new, encoding="utf-8")
            changed.append(f)
    return changed


if __name__ == "__main__":
    old = ('<mark class="mk mk-fondo" data-nota="x">a</mark> <mark class="mk mk-sub">b</mark> <mark class="mk-tacha">c</mark>\n'
           '<aside class="tarjeta" data-x="1"><div class="cuerpo">d</div></aside> <p class="mk-subtle">tarjeta cuerpo</p>')
    new = ('<mark class="mk mk-highlight" data-comment="x">a</mark> <mark class="mk mk-underline">b</mark> <mark class="mk-strike">c</mark>\n'
           '<aside class="card" data-x="1"><div class="card-body">d</div></aside> <p class="mk-subtle">tarjeta cuerpo</p>')
    assert migrate(old) == new and migrate(new) == new
    topics = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "topics"
    changed = run(topics)
    print("\n".join(str(f.relative_to(topics)) for f in changed) or "nothing to migrate")
