#!/usr/bin/env python3
"""Self-check of user font upload (POST /api/font, GET /api/fonts): python3 app/test_fonts.py"""
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
        assert server.save_font("My Font.woff2", WOFF2) == {"fonts": ["My Font.woff2"]}
        server.save_font("b.ttf", b"\0\1\0\0" + b"\0" * 60)
        server.save_font("c.otf", b"OTTO" + b"\0" * 60)
        assert (tmp / "fonts" / "My Font.woff2").read_bytes() == WOFF2
        assert server.list_fonts() == ["My Font.woff2", "b.ttf", "c.otf"]

        assert rejected("notes.txt", WOFF2), "extension not whitelisted"
        assert rejected("fake.ttf", b"<html>not a font</html>"), "magic bytes"
        assert rejected("big.woff2", WOFF2 + b"\0" * server.BODY_LIMIT), "size cap"
        for name in ("../evil.ttf", "../../fonts/x.woff2", "a/b.otf", "..\\x.ttf", ".hidden.ttf", "/etc/x.ttf"):
            assert rejected(name, WOFF2), "path traversal: " + name
        assert server.list_fonts() == ["My Font.woff2", "b.ttf", "c.otf"], "a rejected upload must not write"
        assert not (tmp / "evil.ttf").exists()
    finally:
        server.ROOT = real_root
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_fonts()
    print("ok")
