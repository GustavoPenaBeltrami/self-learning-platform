#!/usr/bin/env python3
import pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import server

WOFF2 = b"wOF2" + b"\0" * 60


def rejected(name, raw):
    try:
        server.save_font(name, raw)
    except ValueError:
        return True
    return False


def test_fonts():
    tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
    real_root, server.ROOT = server.ROOT, tmp
    try:
        assert server.list_fonts() == []
        assert server.save_font("My  Font.woff2", WOFF2) == {"fonts": ["my-font.woff2"]}, "lowercase, spaces to -"
        server.save_font("b.ttf", b"\0\1\0\0" + b"\0" * 60)
        server.save_font("c.otf", b"OTTO" + b"\0" * 60)
        assert (tmp / "fonts" / "my-font.woff2").read_bytes() == WOFF2
        assert server.list_fonts() == ["b.ttf", "c.otf", "my-font.woff2"]
        assert 'url("/fonts/b.ttf")' in server.fonts_css() and ':root[data-font="my-font.woff2"]' in server.fonts_css()

        assert rejected("MY FONT.woff2", WOFF2), "same name in another case must not overwrite"
        assert rejected("Font.TTF", WOFF2), "the extension stays case-sensitive"

        assert rejected("notes.txt", WOFF2), "extension not whitelisted"
        assert rejected("fake.ttf", b"<html>not a font</html>"), "magic bytes"
        assert rejected("big.woff2", WOFF2 + b"\0" * server.BODY_LIMIT), "size cap"
        for name in ("../evil.ttf", "../../fonts/x.woff2", "a/b.otf", "..\\x.ttf", ".hidden.ttf", "/etc/x.ttf"):
            assert rejected(name, WOFF2), "path traversal: " + name
        assert server.list_fonts() == ["b.ttf", "c.otf", "my-font.woff2"], "a rejected upload must not write"
        assert not (tmp / "evil.ttf").exists()
    finally:
        server.ROOT = real_root
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_fonts()
    print("ok")
