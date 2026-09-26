#!/usr/bin/env python3
import contextlib, io, os, pathlib, shutil, sys, tempfile, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import store, voice

downloads = []


def with_temp_root(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real_root, real_engine, real_env, real_mods = store.ROOT, voice.ENGINE, os.environ.pop("NOTES_VOICE_MODEL", None), dict(sys.modules)
        store.ROOT, voice.ENGINE = tmp, "mlx"
        sys.modules["mlx_whisper"] = types.SimpleNamespace()
        sys.modules["huggingface_hub"] = types.SimpleNamespace(snapshot_download=lambda repo_id, local_dir: pathlib.Path(local_dir).mkdir(parents=True) or downloads.append((repo_id, local_dir)))
        downloads.clear()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                f()
        finally:
            store.ROOT, voice.ENGINE = real_root, real_engine
            if real_env is not None:
                os.environ["NOTES_VOICE_MODEL"] = real_env
            sys.modules.clear()
            sys.modules.update(real_mods)
            shutil.rmtree(tmp)
    return wrapped


def answers(*replies):
    replies = list(replies)
    return lambda prompt: replies.pop(0)


@with_temp_root
def test_download_picks_the_engine_repo():
    assert voice.download_voice_model("tiny") == str(store.ROOT / "models" / "whisper-tiny-mlx")
    voice.ENGINE = "cpu"
    assert voice.download_voice_model("turbo") == str(store.ROOT / "models" / "faster-whisper-large-v3-turbo")
    assert [r for r, _ in downloads] == ["mlx-community/whisper-tiny-mlx", "mobiuslabsgmbh/faster-whisper-large-v3-turbo"]
    try:
        voice.download_voice_model("huge")
    except ValueError:
        return
    raise AssertionError("an unknown size must be rejected")


@with_temp_root
def test_online_downloads_turbo_without_asking_sizes():
    s = voice.setup(answers(""))
    assert s["profile"] == "auto" and len(downloads) == 1
    assert s["voice_model"] == "turbo" and downloads[0][1].startswith(str(store.ROOT / "models"))


@with_temp_root
def test_offline_takes_a_local_path_and_rerun_keeps_it():
    local = store.ROOT / "my-model"
    local.mkdir()
    s = voice.setup(answers("3", "/no/such/model", str(local)))
    assert s == {**store.read_settings(), "profile": "offline", "voice_model": str(local)} and not downloads
    assert voice.setup(answers("")) == s, "re-running setup must offer to keep the current choices"
    assert voice.setup(answers("n", "3", "none"))["voice_model"] == "", "none skips dictation"


@with_temp_root
def test_failed_download_degrades_to_os_dictation():
    def fail(repo_id, local_dir):
        raise OSError("offline")
    sys.modules["huggingface_hub"] = types.SimpleNamespace(snapshot_download=fail)
    s = voice.setup(answers("3", "tiny"))
    assert s["profile"] == "offline" and s["voice_model"] == ""


@with_temp_root
def test_no_keeps_asking():
    voice.setup(answers("2"))
    assert voice.setup(answers("n", "3", "none")) == {**store.read_settings(), "profile": "offline", "voice_model": ""}


if __name__ == "__main__":
    test_download_picks_the_engine_repo()
    test_online_downloads_turbo_without_asking_sizes()
    test_offline_takes_a_local_path_and_rerun_keeps_it()
    test_failed_download_degrades_to_os_dictation()
    test_no_keeps_asking()
    print("ok")
