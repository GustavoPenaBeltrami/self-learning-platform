#!/usr/bin/env python3
import json, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
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
    assert server.read_settings() == {"profile": "auto", "theme": "", "ui_font": "mono", "font": "mono", "voice_model": ""}


@with_temp_root
def test_round_trip():
    saved = server.save_settings({"profile": "offline", "theme": "kami", "font": "serif", "junk": 1})
    assert saved == {"profile": "offline", "theme": "kami", "ui_font": "mono", "font": "serif", "voice_model": ""}
    assert server.read_settings() == saved
    assert json.loads((server.ROOT / "settings.json").read_text()) == saved
    assert server.save_settings({"theme": "sumi"})["profile"] == "offline", "a partial write must keep the rest"


@with_temp_root
def test_rejects_unknown_profile():
    try:
        server.save_settings({"profile": "cloud"})
    except ValueError:
        assert not (server.ROOT / "settings.json").exists(), "a rejected write must not touch the file"
        return
    raise AssertionError("should have rejected an unknown profile")


@with_temp_root
def test_rejects_missing_model_folder():
    try:
        server.save_settings({"voice_model": "/no/such/model"})
    except ValueError:
        return
    raise AssertionError("a voice_model path must exist")


if __name__ == "__main__":
    test_defaults_without_file()
    test_round_trip()
    test_rejects_unknown_profile()
    test_rejects_missing_model_folder()
    print("ok")
