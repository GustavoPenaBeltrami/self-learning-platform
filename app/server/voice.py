import os, platform, re, shutil, socket, threading

import store

MODELS = {
    "tiny": {"mlx": "mlx-community/whisper-tiny-mlx", "cpu": "Systran/faster-whisper-tiny", "disk": "~75 MB", "ram": "~1 GB"},
    "base": {"mlx": "mlx-community/whisper-base-mlx", "cpu": "Systran/faster-whisper-base", "disk": "~145 MB", "ram": "~1 GB"},
    "small": {"mlx": "mlx-community/whisper-small-mlx", "cpu": "Systran/faster-whisper-small", "disk": "~480 MB", "ram": "~2 GB"},
    "medium": {"mlx": "mlx-community/whisper-medium-mlx", "cpu": "Systran/faster-whisper-medium", "disk": "~1.5 GB", "ram": "~5 GB"},
    "turbo": {"mlx": "mlx-community/whisper-large-v3-turbo", "cpu": "mobiuslabsgmbh/faster-whisper-large-v3-turbo", "disk": "~1.6 GB", "ram": "~6 GB"},
    "large-v3": {"mlx": "mlx-community/whisper-large-v3-mlx", "cpu": "Systran/faster-whisper-large-v3", "disk": "~3 GB", "ram": "~10 GB"},
}
DEFAULT_SIZE = {"mlx": "turbo", "cpu": "small"}   # ponytail: CPU int8 only, a GPU box still runs small on CPU; device="auto" + cuDNN if CUDA users show up
ENGINE = "mlx" if platform.system() == "Darwin" and platform.machine() == "arm64" else "cpu"
voice_lock = threading.Lock()
cpu_model = None
network = None


class NoDictation(ValueError):
    pass


def engine():
    if ENGINE == "mlx":
        try:
            import mlx_whisper
            return "mlx"
        except ImportError:
            pass
    return "cpu"


def model_dir(size, eng=None):
    return store.ROOT / "models" / MODELS[size][eng or engine()].split("/")[-1]


def reachable():
    try:
        socket.create_connection(("huggingface.co", 443), timeout=1.5).close()
        return True
    except OSError:
        return False


def active_profile():
    global network
    profile = store.read_settings()["profile"]
    if profile != store.AUTO:
        return profile
    if network is None:
        network = reachable()   # ponytail: probed once per server run, reconnecting needs a restart; re-probe on a timer if that matters
    return store.ONLINE if network else store.OFFLINE


def check_voice_model(value):
    if value and value not in MODELS and not os.path.isdir(os.path.expanduser(value)):
        raise ValueError("voice_model must be a size or an existing model folder: " + value)
    return value


def voice_model(eng):
    choice = store.read_settings()["voice_model"] or os.environ.get("NOTES_VOICE_MODEL") or DEFAULT_SIZE[eng]
    if choice not in MODELS:
        return os.path.expanduser(choice)
    if model_dir(choice, eng).is_dir():
        return str(model_dir(choice, eng))
    if active_profile() == store.ONLINE:
        return MODELS[choice][eng]
    try:
        from huggingface_hub import snapshot_download
        return snapshot_download(repo_id=MODELS[choice][eng], local_files_only=True)
    except Exception:
        raise NoDictation(f"dictation model {choice} is not on disk and the profile is offline")


def download_voice_model(size):
    if size not in MODELS:
        raise ValueError("unknown model size: " + str(size))
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise NoDictation("dictation engine missing, run uv run slp")
    snapshot_download(repo_id=MODELS[size][engine()], local_dir=str(model_dir(size)))
    return str(model_dir(size))


def load_cpu_model(model):
    global cpu_model
    try:
        import faster_whisper
    except ImportError:
        raise NoDictation("dictation engine missing, run uv run slp")
    try:
        if not cpu_model or cpu_model[0] != model:
            cpu_model = (model, faster_whisper.WhisperModel(model, device="cpu", compute_type="int8",
                                                            local_files_only=active_profile() == store.OFFLINE))
    except Exception as e:
        raise NoDictation(f"dictation model {model} not available: {e}")
    return cpu_model[1]


def whisper(audio, lang):
    if lang is not None and not re.fullmatch(r"[a-z]{2,3}", lang):
        raise ValueError("lang must be a language code like en")
    eng = engine()
    model = voice_model(eng)
    if eng == "cpu":
        segments, _ = load_cpu_model(model).transcribe(audio, language=lang)
        return [[s.start, s.text.strip()] for s in segments]
    import mlx_whisper
    if isinstance(audio, str):
        try:
            import faster_whisper
            audio = faster_whisper.decode_audio(audio)
        except ImportError:
            pass
    try:
        # ponytail: mlx loads and transcribes in one call, so a transcription error also reads as a missing model; split load_model out if the hint misleads
        r = mlx_whisper.transcribe(audio, path_or_hf_repo=model, language=lang)
    except Exception as e:
        raise NoDictation(f"dictation model {model} not available: {e}")
    return [[s["start"], s["text"].strip()] for s in r["segments"]]


def transcribe(raw, lang=None):
    try:
        import numpy
    except ImportError:
        raise NoDictation("dictation engine missing, run uv run slp")
    with voice_lock:   # ponytail: one transcription at a time, there is a single user
        segments = whisper(numpy.frombuffer(raw, dtype="<f4"), lang)
    return {"text": " ".join(t for _, t in segments).strip(), "segments": segments}


def ram_gb():
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    except (AttributeError, ValueError, OSError):
        return 0   # ponytail: Windows has no sysconf so the suggestion falls to base, read GlobalMemoryStatusEx via ctypes if Windows users need it


def ask_model(ask):
    ram, free = ram_gb(), shutil.disk_usage(store.ROOT).free / 2**30
    print(f"This machine: {ram:.0f} GB RAM, {free:.0f} GB free disk.")
    for size, m in MODELS.items():
        print(f"  {size:8} disk {m['disk']:8} RAM {m['ram']}")
    suggested = "turbo" if ram >= 16 else "small" if ram >= 8 else "base"
    while True:
        choice = ask(f"Dictation model: a size, the path to a model you have, or none [{suggested}] ").strip() or suggested
        try:
            check_voice_model("" if choice == "none" else choice)
            return choice
        except ValueError:
            print("Not a size and no such folder: " + choice)


def setup(ask=input):
    current = store.read_settings()
    if store.settings_file().exists():
        keep = ask(f"Current: profile {current['profile']}, voice_model {current['voice_model'] or 'default'}. Keep? [Y/n] ")
        if keep.strip().lower() in ("", "y", "yes"):
            return current
    reply = ask("Profile: 1) auto (recommended: online when connected)  2) online  3) offline [1] ").strip().lower()
    profile = {"2": store.ONLINE, "3": store.OFFLINE}.get(reply, reply if reply in store.PROFILES else store.AUTO)
    choice = ask_model(ask) if profile == store.OFFLINE else "turbo"
    if choice == "none":
        model = ""
    elif choice not in MODELS:
        model = os.path.abspath(os.path.expanduser(choice))
    else:
        print(f"Downloading {choice} ({MODELS[choice]['disk']})...")
        try:
            download_voice_model(choice)
            model = choice
        except Exception as e:
            model = ""
            print(f"Download failed ({e}). The mic falls back to the OS dictation; run uv run slp setup again to retry.")
    return store.save_settings({"profile": profile, "voice_model": model})
