#!/usr/bin/env python3
"""Self-check of the dictation model resolution and the no-engine fallback: python3 app/test_dictation.py"""
import os, pathlib, shutil, sys, tempfile, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import server


def with_temp_root(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real_root, real_env, real_mods = server.ROOT, os.environ.pop("NOTES_VOICE_MODEL", None), dict(sys.modules)
        server.ROOT, server.cpu_model = tmp, None
        try:
            f()
        finally:
            server.ROOT, server.cpu_model = real_root, None
            os.environ.pop("NOTES_VOICE_MODEL", None)
            if real_env is not None:
                os.environ["NOTES_VOICE_MODEL"] = real_env
            sys.modules.clear()
            sys.modules.update(real_mods)
            shutil.rmtree(tmp)
    return wrapped


@with_temp_root
def test_resolution_order():
    assert server.voice_model(True) == server.VOICE_MODEL
    assert server.voice_model(False) == "small"
    os.environ["NOTES_VOICE_MODEL"] = "turbo"
    assert server.voice_model(False) == "turbo"
    server.save_settings({"voice_model": "~/models/whisper"})
    assert server.voice_model(True) == os.path.expanduser("~/models/whisper"), "settings must win over the env var"


@with_temp_root
def test_local_path_goes_straight_to_the_engine():
    seen = []
    model = types.SimpleNamespace(transcribe=lambda audio, language: ([types.SimpleNamespace(start=0.0, text=" hi ")], None))
    sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=lambda path, **kw: seen.append(path) or model)
    sys.modules["mlx_whisper"] = None
    local = str(server.ROOT / "my-model")
    server.save_settings({"voice_model": local})
    assert server.whisper([], None) == [[0.0, "hi"]]
    assert seen == [local]


@with_temp_root
def test_no_engine_raises_fallback():
    sys.modules["numpy"] = sys.modules["faster_whisper"] = sys.modules["mlx_whisper"] = None
    for call in (lambda: server.transcribe(b""), lambda: server.whisper([], None)):
        try:
            call()
        except server.NoDictation:
            continue
        raise AssertionError("no engine must raise NoDictation")


@with_temp_root
def test_missing_model_raises_fallback():
    def fail(path, **kw):
        raise OSError("offline")
    sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=fail)
    sys.modules["mlx_whisper"] = None
    try:
        server.whisper([], None)
    except server.NoDictation:
        return
    raise AssertionError("a model that can't load must raise NoDictation")


if __name__ == "__main__":
    test_resolution_order()
    test_local_path_goes_straight_to_the_engine()
    test_no_engine_raises_fallback()
    test_missing_model_raises_fallback()
    print("ok")
