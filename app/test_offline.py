#!/usr/bin/env python3
import pathlib, re

APP = pathlib.Path(__file__).resolve().parent
VENDOR = APP / "vendor"
URL = re.compile(r"https?://([^/\s\"'`<>():]+)")
LOADER = re.compile(r"""(?:\b(?:fetch|import|importScripts|url)\(\s*|@import\s+|\b(?:src|href)\s*=\s*)["'`]?(https?://[^\s"'`<>)]+)""")
LOCAL = {"localhost", "127.0.0.1"}


def external(url):
    return URL.match(url).group(1) not in LOCAL


def offenders():
    found = []
    for f in sorted(APP.rglob("*")):
        if f.suffix not in {".html", ".js", ".css", ".py"} or f.name.startswith("test_"):
            continue
        text = f.read_text(errors="ignore")
        # ponytail: in vendored source only loader calls count, a URL built by string concatenation slips through; parse the JS if a library ever does that
        urls = LOADER.findall(text) if VENDOR in f.parents else [m.group(0) for m in URL.finditer(text)]
        found += [f"{f.relative_to(APP)}: {u}" for u in urls if external(u)]
    return found


if __name__ == "__main__":
    bad = offenders()
    assert not bad, "external URLs:\n" + "\n".join(bad)
    print("ok")
