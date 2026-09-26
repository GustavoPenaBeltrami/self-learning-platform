#!/usr/bin/env python3
import json, pathlib, re, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import store

DEFAULTS = {"profile": "auto", "theme": "", "ui_font": "mono", "font": "mono",
            "voice_model": "", "mark_colors": "", "shortcuts": {}, "themes": []}
COLORS = {k: "#123456" for k in store.THEME_COLORS}
MINE = {"name": "my-theme", "dark": True, "colors": COLORS}


def file_of(saved, cards=None):
    return {"global": {k: v for k, v in saved.items() if k not in store.SECTIONS}, "shortcuts": saved["shortcuts"],
            "theme": {"active": saved["theme"], "custom": saved["themes"]}, "cards": cards or {}}


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
    saved = store.save_settings({"profile": "offline", "theme": "my-theme", "themes": [MINE], "font": "serif",
                                 "shortcuts": {"notes.dictate": "ctrl+shift+d", "cards.skip": "k"}, "mark_colors": "#ff0000,#00aa11", "junk": 1})
    assert saved == {**DEFAULTS, "profile": "offline", "theme": "my-theme", "themes": [MINE], "font": "serif",
                     "shortcuts": {"notes.dictate": "ctrl+shift+d", "cards.skip": "k"}, "mark_colors": "#ff0000,#00aa11"}
    assert store.read_settings() == saved
    assert json.loads((store.ROOT / "settings.json").read_text()) == file_of(saved)
    assert store.save_settings({"theme": "sakura"})["profile"] == "offline", "a partial write must keep the rest"
    store.save_settings({"theme": "my-theme"})
    assert rejected({"themes": []}), "the active theme cannot be deleted alone"
    assert store.save_settings({"theme": "", "themes": []})["themes"] == []


@with_temp_root
def test_rejections_leave_the_file_alone():
    for bad in ({"profile": "cloud"}, {"theme": "neon"}, {"theme": "seed"}, {"themes": {}}, {"themes": [{**MINE, "name": "sumi"}]},
                {"themes": [MINE, MINE]}, {"themes": [{**MINE, "name": "My Theme"}]}, {"themes": [{**MINE, "dark": 1}]},
                {"themes": [{**MINE, "colors": {**COLORS, "accent": "#ABCDEF"}}]}, {"themes": [{**MINE, "colors": {"void": "#000000"}}]},
                {"themes": [{**MINE, "extra": 1}]},
                {"shortcuts": "ctrl+m"}, {"shortcuts": {"notes.nope": "ctrl+m"}}, {"shortcuts": {"cards.new": "escape"}},
                {"shortcuts": {"cards.new": "shift+ctrl+n"}}, {"shortcuts": {"cards.new": 3}}, {"shortcuts": {"notes.dictate": "m"}},
                {"shortcuts": {"notes.dictate": "meta+b"}}, {"shortcuts": {"cards.skip": "n"}}, {"shortcuts": {"cards.new": "enter"}},
                {"font": 3}, {"voice_model": "/no/such/model"}, {"mark_colors": "red"}, {"mark_colors": "#ff0000,"},
                {"mark_colors": "#FF0000"}):
        assert rejected(bad), bad
    assert not (store.ROOT / "settings.json").exists(), "a rejected write must not touch the file"
    assert not (store.ROOT / "shortcuts.json").exists()


@with_temp_root
def test_shortcut_scopes():
    assert store.save_settings({"shortcuts": {"cards.skip": "enter"}})["shortcuts"] == {"cards.skip": "enter"}, "enter is free while studying"
    assert store.save_settings({"shortcuts": {"exam.record": "n", "cards.new": "ctrl+alt+n"}})["shortcuts"]["exam.record"] == "n"
    assert store.save_settings({"shortcuts": {}})["shortcuts"] == {}


@with_temp_root
def test_old_dictation_key_migrates():
    f = store.ROOT / "settings.json"
    f.write_text(json.dumps({"theme": "kami", "dictation_key": "shift+alt+d"}))
    assert store.read_settings()["shortcuts"] == {"notes.dictate": "alt+shift+d"}
    f.write_text(json.dumps({"dictation_key": "ctrl+m"}))
    assert store.read_settings()["shortcuts"] == {}
    f.write_text(json.dumps({"dictation_key": "m"}))
    assert store.read_settings()["shortcuts"] == {}
    f.write_text(json.dumps({"dictation_key": "alt+d", "theme": "kami"}))
    saved = store.save_settings({"font": "serif"})
    assert saved["shortcuts"] == {"notes.dictate": "alt+d"} and saved["theme"] == "kami"
    assert "dictation_key" not in json.loads(f.read_text())["global"]
    f.write_text(json.dumps({"global": {}, "shortcuts": {"cards.new": "s"}}))
    assert store.read_settings()["shortcuts"] == {}, "a hand-edited conflict reads as defaults"


@with_temp_root
def test_old_files_merge_into_settings_json():
    f = store.ROOT / "settings.json"
    f.write_text(json.dumps({"theme": "kami", "shortcuts": {"cards.skip": "x"}}))
    assert store.read_settings()["shortcuts"] == {"cards.skip": "x"}
    (store.ROOT / "shortcuts.json").write_text(json.dumps({"cards.skip": "k"}))
    (store.ROOT / "card-config.json").write_text(json.dumps({"intervals": [3, 4]}))
    assert store.read_settings()["shortcuts"] == {"cards.skip": "k"}, "shortcuts.json wins over the flat file"
    assert store.read_card_config()["intervals"] == [3, 4]
    store.save_settings({"font": "serif"})
    assert json.loads(f.read_text()) == file_of({**DEFAULTS, "theme": "kami", "font": "serif", "shortcuts": {"cards.skip": "k"}}, {"intervals": [3, 4]})
    assert not (store.ROOT / "shortcuts.json").exists() and not (store.ROOT / "card-config.json").exists()
    assert store.read_card_config()["intervals"] == [3, 4] and store.read_settings()["theme"] == "kami"


def test_defaults_match_shell_js():
    js = (pathlib.Path(__file__).resolve().parents[1] / "scripts" / "shell.js").read_text()
    rows = re.findall(r"\['([a-z]+\.[a-z]+)', '([^']*)', (?:'[^']*'|\"[^\"]*\"), '([^']*)'(, 1)?\]", js)
    assert {i: (k, m) for i, k, m, fixed in rows if not fixed} == store.SHORTCUTS


@with_temp_root
def test_stale_voice_model_does_not_block_other_keys():
    (store.ROOT / "settings.json").write_text(json.dumps({"voice_model": "/moved/away/model"}))
    assert store.save_settings({"theme": "kami"})["theme"] == "kami"


@with_temp_root
def test_hand_edited_theme_section():
    f = store.ROOT / "settings.json"
    f.write_text(json.dumps({"global": {"theme": "kami", "theme_seed": "#3a6ea5"}}))
    assert store.read_settings()["theme"] == "kami", "the old global.theme still reads"
    f.write_text(json.dumps({"global": {"theme": "seed"}}))
    assert store.read_settings()["theme"] == "", "the removed seed theme reads as auto"
    f.write_text(json.dumps({"global": {}, "theme": {"active": "my-theme", "custom": [MINE]}}))
    assert store.read_settings()["theme"] == "my-theme"
    f.write_text(json.dumps({"global": {}, "theme": {"active": "my-theme", "custom": [{**MINE, "dark": "yes"}]}}))
    assert store.read_settings()["theme"] == "" and store.read_settings()["themes"] == [], "a broken list reads as none"


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
    test_shortcut_scopes()
    test_old_dictation_key_migrates()
    test_old_files_merge_into_settings_json()
    test_defaults_match_shell_js()
    test_stale_voice_model_does_not_block_other_keys()
    test_hand_edited_theme_section()
    test_corrupt_file_reads_as_defaults()
    print("ok")
