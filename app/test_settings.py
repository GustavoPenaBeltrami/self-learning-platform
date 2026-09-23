#!/usr/bin/env python3
"""Self-check of the settings store (GET/POST /api/settings): python3 app/test_settings.py"""
import json, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import server


def with_temp_root(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real_root = server.ROOT
        server.ROOT = tmp
        try:
            f()
        finally:
            server.ROOT = real_root
            shutil.rmtree(tmp)
    return wrapped


@with_temp_root
def test_defaults_without_file():
    assert not (server.ROOT / "settings.json").exists()
    assert server.read_settings() == {"profile": "online", "theme": "", "font": "mono"}


@with_temp_root
def test_round_trip():
    saved = server.save_settings({"profile": "offline", "theme": "sakura", "font": "serif", "junk": 1})
    assert saved == {"profile": "offline", "theme": "sakura", "font": "serif"}
    assert server.read_settings() == saved
    assert json.loads((server.ROOT / "settings.json").read_text()) == saved
    assert server.save_settings({"theme": "amber"})["profile"] == "offline", "a partial write must keep the rest"


@with_temp_root
def test_rejects_unknown_profile():
    try:
        server.save_settings({"profile": "cloud"})
    except ValueError:
        assert not (server.ROOT / "settings.json").exists(), "a rejected write must not touch the file"
        return
    raise AssertionError("should have rejected an unknown profile")


if __name__ == "__main__":
    test_defaults_without_file()
    test_round_trip()
    test_rejects_unknown_profile()
    print("ok")
