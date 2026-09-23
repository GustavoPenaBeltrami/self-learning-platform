#!/usr/bin/env python3
import os, pathlib, shutil, sys, tempfile, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import server


def with_temp_root(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real_root, real_env, real_mods = server.ROOT, os.environ.pop("NOTES_VOICE_MODEL", None), dict(sys.modules)
        server.ROOT, server.cpu_model, server.network = tmp, None, True
        try:
            f()
        finally:
            server.ROOT, server.cpu_model, server.network = real_root, None, None
            os.environ.pop("NOTES_VOICE_MODEL", None)
            if real_env is not None:
                os.environ["NOTES_VOICE_MODEL"] = real_env
            sys.modules.clear()
            sys.modules.update(real_mods)
            shutil.rmtree(tmp)
    return wrapped


@with_temp_root
def test_resolution_order():
    assert server.voice_model("mlx") == "mlx-community/whisper-large-v3-turbo", "default: turbo on the GPU"
    assert server.voice_model("cpu") == "Systran/faster-whisper-small", "default: small on CPU"
    os.environ["NOTES_VOICE_MODEL"] = "tiny"
    assert server.voice_model("cpu") == "Systran/faster-whisper-tiny", "the env var beats the default"
    assert server.voice_model("mlx") == "mlx-community/whisper-tiny-mlx", "a size maps to the engine's repo"
    local = server.ROOT / "whisper"
    local.mkdir()
    server.save_settings({"voice_model": str(local)})
    assert server.voice_model("mlx") == str(local), "settings beat the env var"


@with_temp_root
def test_downloaded_size_is_used_from_models():
    server.model_dir("small", "cpu").mkdir(parents=True)
    server.save_settings({"voice_model": "small"})
    assert server.voice_model("cpu") == str(server.model_dir("small", "cpu"))


@with_temp_root
def test_offline_never_fetches():
    calls = []
    def cache_only(repo_id, local_files_only=False):
        calls.append(local_files_only)
        raise OSError("not cached")
    sys.modules["huggingface_hub"] = types.SimpleNamespace(snapshot_download=cache_only)
    server.save_settings({"profile": "offline"})
    try:
        server.voice_model("cpu")
    except server.NoDictation:
        assert calls == [True], "offline must look in the cache only"
    else:
        raise AssertionError("a size not on disk must raise NoDictation offline")
    server.save_settings({"profile": "auto"})
    server.network = False
    try:
        server.voice_model("cpu")
    except server.NoDictation:
        pass
    else:
        raise AssertionError("auto with no network acts as offline")
    seen = []
    sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=lambda path, **kw: seen.append(kw) or 1/0)
    sys.modules["mlx_whisper"] = None
    local = server.ROOT / "m"
    local.mkdir()
    server.save_settings({"voice_model": str(local)})
    try:
        server.whisper([], None)
    except server.NoDictation:
        pass
    assert seen[0]["local_files_only"] is True


@with_temp_root
def test_local_path_goes_straight_to_the_engine():
    seen = []
    model = types.SimpleNamespace(transcribe=lambda audio, language: ([types.SimpleNamespace(start=0.0, text=" hi ")], None))
    sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=lambda path, **kw: seen.append(path) or model)
    sys.modules["mlx_whisper"] = None
    local = str(server.ROOT / "my-model")
    pathlib.Path(local).mkdir()
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
    test_downloaded_size_is_used_from_models()
    test_offline_never_fetches()
    test_local_path_goes_straight_to_the_engine()
    test_no_engine_raises_fallback()
    test_missing_model_raises_fallback()
    print("ok")
