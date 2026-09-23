#!/usr/bin/env python3
"""Self-check of ./notes setup, profile defaults and the model download (faked, never hits the network): python3 app/test_setup.py"""
import os, pathlib, shutil, sys, tempfile, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import server

downloads = []


def with_temp_root(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real_root, real_env, real_hub = server.ROOT, os.environ.pop("NOTES_VOICE_MODEL", None), sys.modules.get("huggingface_hub")
        server.ROOT = tmp
        sys.modules["huggingface_hub"] = types.SimpleNamespace(snapshot_download=lambda repo_id, local_dir: downloads.append((repo_id, local_dir)))
        downloads.clear()
        try:
            f()
        finally:
            server.ROOT = real_root
            if real_env is not None:
                os.environ["NOTES_VOICE_MODEL"] = real_env
            sys.modules.pop("huggingface_hub")
            if real_hub:
                sys.modules["huggingface_hub"] = real_hub
            shutil.rmtree(tmp)
    return wrapped


def answers(*replies):
    replies = list(replies)
    return lambda prompt: replies.pop(0)


@with_temp_root
def test_profile_defaults():
    assert server.profile_defaults("online") == {"voice_model": "turbo", "sources_mode": "both"}
    assert server.profile_defaults("offline") == {"voice_model": "", "sources_mode": "local"}
    assert server.voice_model(False) == "turbo", "online with no voice_model: the largest model"
    server.save_settings({"profile": "offline"})
    assert server.voice_model(False) == "small", "offline with no voice_model: the engine default"


@with_temp_root
def test_download_picks_the_engine_repo():
    assert server.download_voice_model("tiny", gpu=True) == str(server.ROOT / "models" / "whisper-tiny-mlx")
    assert server.download_voice_model("turbo", gpu=False) == str(server.ROOT / "models" / "faster-whisper-large-v3-turbo")
    assert [r for r, _ in downloads] == ["mlx-community/whisper-tiny-mlx", "mobiuslabsgmbh/faster-whisper-large-v3-turbo"]
    try:
        server.download_voice_model("huge")
    except ValueError:
        return
    raise AssertionError("an unknown size must be rejected")


@with_temp_root
def test_online_downloads_turbo_without_asking_sizes():
    s = server.setup(answers(""))
    assert s["profile"] == "online" and len(downloads) == 1
    assert s["voice_model"] == downloads[0][1] and s["voice_model"].startswith(str(server.ROOT / "models"))


@with_temp_root
def test_offline_takes_a_local_path_and_rerun_keeps_it():
    local = server.ROOT / "my-model"
    local.mkdir()
    s = server.setup(answers("2", "/no/such/model", str(local)))
    assert s == {**server.read_settings(), "profile": "offline", "voice_model": str(local)} and not downloads
    assert server.setup(answers("")) == s, "re-running setup must offer to keep the current choices"
    assert server.setup(answers("n", "2", "none"))["voice_model"] == "", "none skips dictation"


@with_temp_root
def test_failed_download_degrades_to_os_dictation():
    def fail(repo_id, local_dir):
        raise OSError("offline")
    sys.modules["huggingface_hub"] = types.SimpleNamespace(snapshot_download=fail)
    s = server.setup(answers("2", "tiny"))
    assert s["profile"] == "offline" and s["voice_model"] == ""


if __name__ == "__main__":
    test_profile_defaults()
    test_download_picks_the_engine_repo()
    test_online_downloads_turbo_without_asking_sizes()
    test_offline_takes_a_local_path_and_rerun_keeps_it()
    test_failed_download_degrades_to_os_dictation()
    print("ok")
