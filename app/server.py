#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "mlx-whisper; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper; sys_platform != 'win32' or platform_machine != 'ARM64'",
# ]
# ///
"""Local server for the study system. Stdlib only: python3 app/server.py

Dictation is the only thing that needs more: mlx-whisper on Apple Silicon Macs,
faster-whisper everywhere else. `./notes` (uv run) brings the right one;
without it everything works except the microphone.
"""
import base64, datetime, hashlib, http.server, json, os, pathlib, platform, re, shutil, socket, sys, threading, urllib.parse, webbrowser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import text

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = (ROOT / "topics").resolve()   # ponytail: a symlinked topics/ is resolved once at start, relinking it needs a restart, resolve per request if that matters
PORT = 8321
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
BODY_LIMIT = 20 * 1024 * 1024   # ponytail: one flat cap for every POST, single local user
AUDIO_EXT = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "mp4",
             "audio/wav": "wav", "audio/x-wav": "wav"}


def audio_ext(mime):
    """MediaRecorder mime ('audio/webm;codecs=opus' -> 'webm'). Rejects anything not whitelisted."""
    ext = AUDIO_EXT.get(mime.split(";")[0].strip().lower())
    if not ext:
        raise ValueError("audio type not allowed: " + mime)
    return ext


class NoDictation(ValueError):
    pass


def model_dir(size, engine=None):
    return ROOT / "models" / MODELS[size][engine or ENGINE].split("/")[-1]


def voice_model(engine):
    choice = read_settings()["voice_model"] or os.environ.get("NOTES_VOICE_MODEL") or DEFAULT_SIZE[engine]
    if choice not in MODELS:
        return os.path.expanduser(choice)
    if model_dir(choice, engine).is_dir():
        return str(model_dir(choice, engine))
    if active_profile() == "online":
        return MODELS[choice][engine]
    try:
        from huggingface_hub import snapshot_download
        return snapshot_download(repo_id=MODELS[choice][engine], local_files_only=True)
    except Exception:
        raise NoDictation(f"dictation model {choice} is not on disk and the profile is offline")


def download_voice_model(size):
    if size not in MODELS:
        raise ValueError("unknown model size: " + str(size))
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise NoDictation("dictation engine missing, start with ./notes")
    snapshot_download(repo_id=MODELS[size][ENGINE], local_dir=str(model_dir(size)))
    return str(model_dir(size))


def whisper(audio, lang):
    global cpu_model
    try:
        import faster_whisper
    except ImportError:
        raise NoDictation("dictation engine missing, start with ./notes")
    if isinstance(audio, str):
        audio = faster_whisper.decode_audio(audio)
    try:
        import mlx_whisper
    except ImportError:
        mlx_whisper = None
    model = voice_model("mlx" if mlx_whisper else "cpu")
    try:
        if mlx_whisper:
            # ponytail: mlx loads and transcribes in one call, so a transcription error also reads as a missing model; split load_model out if the hint misleads
            r = mlx_whisper.transcribe(audio, path_or_hf_repo=model, language=lang)
            return [[s["start"], s["text"].strip()] for s in r["segments"]]
        if not cpu_model or cpu_model[0] != model:
            cpu_model = (model, faster_whisper.WhisperModel(model, device="cpu", compute_type="int8",
                                                            local_files_only=active_profile() == "offline"))
    except Exception as e:
        raise NoDictation(f"dictation model {model} not available: {e}")
    segments, _ = cpu_model[1].transcribe(audio, language=lang)
    return [[s.start, s.text.strip()] for s in segments]


def transcribe(raw, lang=None):
    """float32 mono at 16 kHz, as the browser sends it. lang None = auto-detect."""
    try:
        import numpy   # in here: the rest of the server doesn't need it
    except ImportError:
        raise NoDictation("dictation engine missing, start with ./notes")
    with voice_lock:   # ponytail: one transcription at a time, there is a single user
        segments = whisper(numpy.frombuffer(raw, dtype="<f4"), lang)
    # segments [start_s, text]: live dictation pins the old ones and trims the audio there
    return {"text": " ".join(t for _, t in segments).strip(), "segments": segments}


AUTO, ONLINE, OFFLINE = PROFILES = ("auto", "online", "offline")
SETTINGS = {"profile": AUTO, "theme": "", "font": "mono", "voice_model": ""}
network = None


def reachable():
    try:
        socket.create_connection(("huggingface.co", 443), timeout=1.5).close()
        return True
    except OSError:
        return False


def active_profile():
    global network
    profile = read_settings()["profile"]
    if profile != AUTO:
        return profile
    if network is None:
        network = reachable()   # ponytail: probed once per server run, reconnecting needs a restart; re-probe on a timer if that matters
    return ONLINE if network else OFFLINE


def check_voice_model(value):
    if value and value not in MODELS and not os.path.isdir(os.path.expanduser(value)):
        raise ValueError("voice_model must be a size or an existing model folder: " + value)
    return value


def ram_gb():
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    except (AttributeError, ValueError, OSError):
        return 0   # ponytail: Windows has no sysconf so the suggestion falls to base, read GlobalMemoryStatusEx via ctypes if Windows users need it


def setup(ask=input):
    current = read_settings()
    if (ROOT / "settings.json").exists():
        keep = ask(f"Current: profile {current['profile']}, voice_model {current['voice_model'] or 'default'}. Keep? [Y/n] ")
        if keep.strip().lower() in ("", "y", "yes"):
            return current
    reply = ask("Profile: 1) auto (recommended: online when connected)  2) online  3) offline [1] ").strip().lower()
    profile = {"2": ONLINE, "3": OFFLINE}.get(reply, reply if reply in PROFILES else AUTO)
    choice = "turbo"
    if profile == OFFLINE:
        ram, free = ram_gb(), shutil.disk_usage(ROOT).free / 2**30
        print(f"This machine: {ram:.0f} GB RAM, {free:.0f} GB free disk.")
        for size, m in MODELS.items():
            print(f"  {size:8} disk {m['disk']:8} RAM {m['ram']}")
        suggested = "turbo" if ram >= 16 else "small" if ram >= 8 else "base"
    while profile == OFFLINE:
        choice = ask(f"Dictation model: a size, the path to a model you have, or none [{suggested}] ").strip() or suggested
        try:
            check_voice_model("" if choice == "none" else choice)
            break
        except ValueError:
            print("Not a size and no such folder: " + choice)
    if choice == "none":
        model = ""
    elif choice not in MODELS:
        model = os.path.abspath(os.path.expanduser(choice))
    else:
        print(f"Downloading {choice} ({MODELS[choice]['disk']})...")
        try:
            model = download_voice_model(choice)
        except Exception as e:
            model = ""
            print(f"Download failed ({e}). The mic falls back to the OS dictation; run ./notes setup again to retry.")
    return save_settings({"profile": profile, "voice_model": model})


def read_settings():
    file = ROOT / "settings.json"
    saved = json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}
    return {k: saved.get(k, v) for k, v in SETTINGS.items()}


def save_settings(data):
    settings = read_settings()
    settings.update({k: data[k] for k in SETTINGS if k in data})
    if settings["profile"] not in PROFILES:
        raise ValueError("unknown profile: " + str(settings["profile"]))
    if not all(isinstance(v, str) for v in settings.values()):
        raise ValueError("settings values must be strings")
    check_voice_model(settings["voice_model"])
    (ROOT / "settings.json").write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return settings


FONT_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*\.(woff2|ttf|otf)")
FONT_MAGIC = (b"wOF2", b"OTTO", b"\0\1\0\0", b"true")


def font_name(upload):
    stem, dot, ext = upload.rpartition(".")
    return re.sub(r"\s+", "-", stem.strip().lower()) + dot + ext


def list_fonts():
    d = ROOT / "fonts"
    return sorted(f.name for f in d.iterdir() if f.is_file() and FONT_NAME.fullmatch(f.name)) if d.is_dir() else []


def fonts_css():
    return "\n".join(f'@font-face {{ font-family: "{f}"; src: url("/fonts/{f}"); }}\n'
                     f':root[data-font="{f}"] {{ --reading-font: "{f}", var(--mono); }}' for f in list_fonts())


def save_font(upload, raw):
    name = font_name(upload)
    if not FONT_NAME.fullmatch(name):
        raise ValueError("font name not allowed (a .woff2, .ttf or .otf file name, no folders): " + upload)
    if len(raw) > BODY_LIMIT:
        raise ValueError("font too large")
    if not raw.startswith(FONT_MAGIC):
        raise ValueError("not a font file: " + upload)
    d = ROOT / "fonts"
    if (d / name).exists():
        raise ValueError(f"a font named {name} already exists: rename the file or delete fonts/{name}")
    d.mkdir(exist_ok=True)
    (d / name).write_bytes(raw)
    return {"fonts": list_fonts()}


def folder(slug):
    """Topic folder. Rejects anything that escapes topics/."""
    d = (TOPICS / slug).resolve()
    if d.parent != TOPICS or not d.is_dir():
        raise ValueError("no such topic: " + slug)
    return d


TYPES = ("book", "certification", "documentation", "course")


def meta(d):
    """What describes the topic. `order` rules the lists; without it, it goes last."""
    file = d / "topic.json"
    saved = json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}
    title = d.name if " " in d.name else d.name.replace("-", " ").capitalize()
    return {"title": saved.get("title") or title,
            "subtitle": saved.get("subtitle", ""),
            "type": saved.get("type", "book"),
            "order": saved.get("order", 999),
            "links": saved.get("links", []),
            "language": saved.get("language", {})}


def resources(d):
    """PDFs, loose notes, whatever you drop in resources/. Served as is."""
    res = d / "resources"
    if not res.is_dir():
        return []
    return [{"name": f.name,
             "path": f"/topics/{urllib.parse.quote(d.name)}/resources/{urllib.parse.quote(f.name)}",
             "kb": round(f.stat().st_size / 1024)}
            for f in sorted(res.iterdir()) if f.is_file() and not f.name.startswith(".")]


def sort_topics(items):
    return sorted(items, key=lambda l: (l["order"], text.slug(l["title"])))


EXT = {"png": ".png", "jpeg": ".jpg", "jpg": ".jpg", "gif": ".gif",
       "webp": ".webp", "avif": ".avif", "svg+xml": ".svg"}
IMG_NAME = re.compile(r"^[0-9a-f]{16}\.[a-z]+$")


def to_url(html, slug):
    """notes/img/x.png -> URL the browser can request."""
    return html.replace('src="img/', f'src="/topics/{urllib.parse.quote(slug)}/notes/img/')


def to_path(html, slug):
    return html.replace(f'src="/topics/{urllib.parse.quote(slug)}/notes/img/', 'src="img/')


def extract_images(html, dest):
    """Pulls pasted images out of the .md and stores them as separate files.

    The name is the content hash: pasting the same screenshot twice doesn't
    duplicate the file, and the .md keeps a short reference instead of
    hundreds of KB of base64.
    """
    def save(m):
        raw = base64.b64decode(m.group(2))
        name = hashlib.sha1(raw).hexdigest()[:16] + EXT.get(m.group(1), ".bin")
        dest.mkdir(parents=True, exist_ok=True)
        file = dest / name
        if not file.exists():
            file.write_bytes(raw)
        return f'src="img/{name}"'

    return re.sub(r'src="data:image/([a-z+]+);base64,([^"]+)"', save, html)


def sections(d):
    return sorted((d / "notes").glob("*.md"))


def headings(d):
    return [re.sub(r"<[^>]+>|[*_~`\[\]]", "", l[2:]).strip()
            for f in sections(d) for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("# ")]


def topics():
    out = [{"slug": d.name, **meta(d), "sections": len(sections(d)),
            "resources": len(resources(d)), "index": headings(d)}
           for d in TOPICS.glob("*") if d.is_dir()]
    return sort_topics(out)


def read_topic(slug):
    d = folder(slug)
    parts = [text.md_to_html(f.read_text(encoding="utf-8")) for f in sections(d)]
    return {"slug": slug, **meta(d), "resources": resources(d),
            "html": to_url("\n".join(parts), slug)}


def save_topic(slug, data):
    d = folder(slug)
    notes = d / "notes"
    notes.mkdir(exist_ok=True)
    file = d / "topic.json"                 # keeps `order`, `language` and the rest, which don't travel in the editor
    saved = json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}
    saved.update({k: data[k] for k in ("title", "subtitle") if k in data})
    file.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    html = extract_images(to_path(data.get("html", ""), slug), notes / "img")
    used = set(re.findall(r'src="img/([^"]+)"', html))   # before splitting: html is reused below

    written = set()
    for i, (title, chunk) in enumerate(text.split_by_h1(html), 1):
        name = f"{i:02d}-{text.slug(title)}.md"
        (notes / name).write_text(text.html_to_md(chunk), encoding="utf-8")
        written.add(name)
    for old in notes.glob("*.md"):          # deleted or renamed sections
        if old.name not in written:
            old.unlink()

    # images no .md references anymore. Only the ones the server generated,
    # in case you ever drop a file of your own in that folder.
    img = notes / "img"
    if img.is_dir():
        for f in img.iterdir():
            if f.is_file() and f.name not in used and IMG_NAME.match(f.name):
                f.unlink()
    return {"ok": True, "sections": sorted(written)}


def exam_index():
    out = [{"slug": d.name, **meta(d),
            "exams": [{"path": f"topics/{d.name}/exams/{f.parent.name}/exam.json",
                       "title": json.loads(f.read_text(encoding="utf-8")).get("title", f.parent.name)}
                      for f in sorted((d / "exams").glob("*/exam.json"))]}
           for d in TOPICS.glob("*") if d.is_dir()]
    return {"topics": sort_topics(out)}


def exam_folder(d, exam):
    """Exam folder inside the topic. Same escape check as folder()."""
    c = (d / "exams" / exam).resolve()
    if c.parent != (d / "exams").resolve() or not (c / "exam.json").is_file():
        raise ValueError("no such exam: " + exam)
    return c


def save_attempt(slug, exam, answers):
    """Writes exams/<exam>/attempts/<date-to-the-minute>.json. Returns the relative path.

    Oral answers with audio are saved as a separate file
    (attempts/<date>-p<i>.<ext>); the JSON keeps the name, not the base64.
    """
    c = exam_folder(folder(slug), exam)
    attempts = c / "attempts"
    attempts.mkdir(exist_ok=True)
    date = datetime.datetime.now().strftime("%Y-%m-%dT%H%M")
    for a in answers:
        if a.get("type") == "oral" and "audio" in a:
            ext = audio_ext(a.pop("mime", ""))
            name = f"{date}-p{a['i']}.{ext}"
            (attempts / name).write_bytes(base64.b64decode(a.pop("audio")))
            a["audio"] = name
    path = attempts / (date + ".json")
    path.write_text(json.dumps({"exam": exam, "answers": answers}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "topics/" + path.relative_to(TOPICS).as_posix()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def respond(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])
        try:
            if path == "/settings":
                self.send_response(302)
                self.send_header("Location", "/app/settings.html")
                return self.end_headers()
            if path == "/api/settings":
                return self.respond(200, {**read_settings(), "active_profile": active_profile()})
            if path == "/api/voice-models":
                return self.respond(200, {k: {"disk": m["disk"], "ram": m["ram"]} for k, m in MODELS.items()})
            if path == "/api/fonts":
                return self.respond(200, {"fonts": list_fonts()})
            if path == "/api/fonts.css":
                body = fonts_css().encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/css; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return self.wfile.write(body)
            if path == "/api/index":
                return self.respond(200, exam_index())
            if path == "/api/topics":
                return self.respond(200, {"topics": topics()})
            if path.startswith("/api/topic/"):
                return self.respond(200, read_topic(path[len("/api/topic/"):]))
        except Exception as e:
            return self.respond(400, {"error": str(e)})
        return super().do_GET()

    def do_POST(self):
        path, _, query = self.path.partition("?")
        path = urllib.parse.unquote(path)
        try:
            length = int(self.headers["Content-Length"])
            if length > BODY_LIMIT:
                return self.respond(400, {"error": "body too large"})
            raw = self.rfile.read(length)
            if path == "/api/voice":
                lang = urllib.parse.parse_qs(query).get("lang", [None])[0]
                try:
                    return self.respond(200, transcribe(raw, lang))
                except NoDictation as e:
                    return self.respond(503, {"error": str(e), "fallback": True})
            if path == "/api/settings":
                return self.respond(200, save_settings(json.loads(raw)))
            if path == "/api/voice-model/download":
                return self.respond(200, save_settings({"voice_model": download_voice_model(json.loads(raw).get("size"))}))
            if path == "/api/font":
                return self.respond(200, save_font(urllib.parse.parse_qs(query).get("name", [""])[0], raw))
            if path == "/api/attempt":
                data = json.loads(raw)
                return self.respond(200, {"path": save_attempt(data["slug"], data["exam"], data["answers"])})
            if not path.startswith("/api/topic/"):
                return self.respond(404, {"error": "not found"})
            self.respond(200, save_topic(path[len("/api/topic/"):], json.loads(raw)))
        except Exception as e:
            self.respond(400, {"error": str(e)})

    def end_headers(self):
        if self.path.endswith((".html", ".css", ".js")):
            self.send_header("Cache-Control", "no-store")   # edit and reload, no hard refresh
        super().end_headers()

    def log_message(self, *a):
        pass  # ponytail: no console noise; remove the pass to debug


if __name__ == "__main__":
    if sys.argv[1:2] == ["--setup"]:
        print("Setup done:", json.dumps(setup()), "\nStart the app with ./notes")
        sys.exit(0)
    if sys.argv[1:2] == ["--transcribe"]:
        print(" ".join(t for _, t in whisper(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)).strip())
        sys.exit(0)
    print(f"Profile: {active_profile()}")
    page = sys.argv[1] if len(sys.argv) > 1 else ""
    url = f"http://localhost:{PORT}/{page}"
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        # ponytail: a server is already up, just open the page
        print(f"A server was already running on {PORT}. Opening {url}")
        webbrowser.open(url)
        sys.exit(0)
    print(f"Study app at {url}  (ctrl+c to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")  # ctrl+c without traceback
