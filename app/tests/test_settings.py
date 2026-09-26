#!/usr/bin/env python3
import json, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import store

DEFAULTS = {"profile": "auto", "theme": "", "theme_seed": "", "ui_font": "mono", "font": "mono",
            "voice_model": "", "dictation_key": "ctrl+m"}


def with_temp_root(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real_root = store.ROOT
        store.ROOT = tmp
        try:
            f()
        finally:
            store.ROOT = real_root
            shutil.rmtree(tmp)
    return wrapped


def rejected(data):
    try:
        store.save_settings(data)
    except ValueError:
        return True
    return False


@with_temp_root
def test_defaults_without_file():
    assert not (store.ROOT / "settings.json").exists()
    assert store.read_settings() == DEFAULTS


@with_temp_root
def test_round_trip():
    saved = store.save_settings({"profile": "offline", "theme": "seed", "theme_seed": "#3a6ea5", "font": "serif",
                                 "dictation_key": "ctrl+shift+d", "junk": 1})
    assert saved == {**DEFAULTS, "profile": "offline", "theme": "seed", "theme_seed": "#3a6ea5", "font": "serif",
                     "dictation_key": "ctrl+shift+d"}
    assert store.read_settings() == saved
    assert json.loads((store.ROOT / "settings.json").read_text()) == saved
    assert store.save_settings({"theme": "sumi"})["profile"] == "offline", "a partial write must keep the rest"


@with_temp_root
def test_rejections_leave_the_file_alone():
    for bad in ({"profile": "cloud"}, {"theme": "neon"}, {"theme_seed": "red"}, {"theme_seed": "#12345"},
                {"dictation_key": "m"}, {"dictation_key": "ctrl+"}, {"dictation_key": "hyper+m"},
                {"font": 3}, {"voice_model": "/no/such/model"}):
        assert rejected(bad), bad
    assert not (store.ROOT / "settings.json").exists(), "a rejected write must not touch the file"


@with_temp_root
def test_stale_voice_model_does_not_block_other_keys():
    (store.ROOT / "settings.json").write_text(json.dumps({"voice_model": "/moved/away/model"}))
    assert store.save_settings({"theme": "kami"})["theme"] == "kami"


@with_temp_root
def test_corrupt_file_reads_as_defaults():
    (store.ROOT / "settings.json").write_text('{"theme": "ka')
    assert store.read_settings() == DEFAULTS
    (store.ROOT / "settings.json").write_text('["not", "a", "dict"]')
    assert store.read_settings() == DEFAULTS
    assert store.save_settings({"theme": "kami"})["theme"] == "kami"


if __name__ == "__main__":
    test_defaults_without_file()
    test_round_trip()
    test_rejections_leave_the_file_alone()
    test_stale_voice_model_does_not_block_other_keys()
    test_corrupt_file_reads_as_defaults()
    print("ok")
