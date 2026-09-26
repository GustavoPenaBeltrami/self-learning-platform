#!/usr/bin/env python3
import os, pathlib, shutil, sys, tempfile, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import store, voice


def with_temp_root(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real_root, real_env, real_mods = store.ROOT, os.environ.pop("NOTES_VOICE_MODEL", None), dict(sys.modules)
        store.ROOT, voice.cpu_model, voice.network = tmp, None, True
        try:
            f()
        finally:
            store.ROOT, voice.cpu_model, voice.network = real_root, None, None
            os.environ.pop("NOTES_VOICE_MODEL", None)
            if real_env is not None:
                os.environ["NOTES_VOICE_MODEL"] = real_env
            sys.modules.clear()
            sys.modules.update(real_mods)
            shutil.rmtree(tmp)
    return wrapped


@with_temp_root
def test_resolution_order():
    assert voice.voice_model("mlx") == "mlx-community/whisper-large-v3-turbo", "default: turbo on the GPU"
    assert voice.voice_model("cpu") == "Systran/faster-whisper-small", "default: small on CPU"
    os.environ["NOTES_VOICE_MODEL"] = "tiny"
    assert voice.voice_model("cpu") == "Systran/faster-whisper-tiny", "the env var beats the default"
    assert voice.voice_model("mlx") == "mlx-community/whisper-tiny-mlx", "a size maps to the engine's repo"
    local = store.ROOT / "whisper"
    local.mkdir()
    store.save_settings({"voice_model": str(local)})
    assert voice.voice_model("mlx") == str(local), "settings beat the env var"


@with_temp_root
def test_downloaded_size_is_used_from_models():
    voice.model_dir("small", "cpu").mkdir(parents=True)
    store.save_settings({"voice_model": "small"})
    assert voice.voice_model("cpu") == str(voice.model_dir("small", "cpu"))


@with_temp_root
def test_offline_never_fetches():
    calls = []
    def cache_only(repo_id, local_files_only=False):
        calls.append(local_files_only)
        raise OSError("not cached")
    sys.modules["huggingface_hub"] = types.SimpleNamespace(snapshot_download=cache_only)
    store.save_settings({"profile": "offline"})
    try:
        voice.voice_model("cpu")
    except voice.NoDictation:
        assert calls == [True], "offline must look in the cache only"
    else:
        raise AssertionError("a size not on disk must raise NoDictation offline")
    store.save_settings({"profile": "auto"})
    voice.network = False
    try:
        voice.voice_model("cpu")
    except voice.NoDictation:
        pass
    else:
        raise AssertionError("auto with no network acts as offline")
    seen = []
    sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=lambda path, **kw: seen.append(kw) or 1/0)
    sys.modules["mlx_whisper"] = None
    local = store.ROOT / "m"
    local.mkdir()
    store.save_settings({"voice_model": str(local)})
    try:
        voice.whisper([], None)
    except voice.NoDictation:
        pass
    assert seen[0]["local_files_only"] is True


@with_temp_root
def test_local_path_goes_straight_to_the_engine():
    seen = []
    model = types.SimpleNamespace(transcribe=lambda audio, language: ([types.SimpleNamespace(start=0.0, text=" hi ")], None))
    sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=lambda path, **kw: seen.append(path) or model)
    sys.modules["mlx_whisper"] = None
    local = str(store.ROOT / "my-model")
    pathlib.Path(local).mkdir()
    store.save_settings({"voice_model": local})
    assert voice.whisper([], None) == [[0.0, "hi"]]
    assert seen == [local]


@with_temp_root
def test_no_engine_raises_fallback():
    sys.modules["numpy"] = sys.modules["faster_whisper"] = sys.modules["mlx_whisper"] = None
    for call in (lambda: voice.transcribe(b""), lambda: voice.whisper([], None)):
        try:
            call()
        except voice.NoDictation:
            continue
        raise AssertionError("no engine must raise NoDictation")


@with_temp_root
def test_missing_model_raises_fallback():
    def fail(path, **kw):
        raise OSError("offline")
    sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=fail)
    sys.modules["mlx_whisper"] = None
    try:
        voice.whisper([], None)
    except voice.NoDictation:
        return
    raise AssertionError("a model that can't load must raise NoDictation")


@with_temp_root
def test_bad_lang_is_rejected():
    try:
        voice.whisper([], "en;rm")
    except voice.NoDictation:
        raise AssertionError("a bad lang is bad input, not a missing engine")
    except ValueError:
        return
    raise AssertionError("lang must be validated")


if __name__ == "__main__":
    test_resolution_order()
    test_downloaded_size_is_used_from_models()
    test_offline_never_fetches()
    test_local_path_goes_straight_to_the_engine()
    test_no_engine_raises_fallback()
    test_missing_model_raises_fallback()
    test_bad_lang_is_rejected()
    print("ok")
