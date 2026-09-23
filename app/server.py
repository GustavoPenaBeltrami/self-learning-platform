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
faster-whisper everywhere else. `npm run app` (uv run) brings the right one;
without it everything works except the microphone.
"""
import base64, datetime, hashlib, http.server, json, os, pathlib, re, sys, threading, urllib.parse, webbrowser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import text

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = ROOT / "topics"
PORT = 8321
VOICE_MODEL = "mlx-community/whisper-large-v3-turbo"   # ~1.6 GB, downloaded the first time
CPU_VOICE_MODEL = "small"   # ponytail: CPU int8 only, set voice_model=turbo on a fast box; CUDA needs device="auto" + cuDNN
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
    """No engine or no model: the mic falls back to the OS dictation."""


def voice_model(gpu):
    """settings.json voice_model, then NOTES_VOICE_MODEL, then the engine default. A local path is used as-is."""
    model = read_settings()["voice_model"] or os.environ.get("NOTES_VOICE_MODEL") or (VOICE_MODEL if gpu else CPU_VOICE_MODEL)
    return os.path.expanduser(model)


def whisper(audio, lang):
    global cpu_model
    try:
        import faster_whisper
    except ImportError:
        raise NoDictation("dictation engine missing, start with npm run app")
    if isinstance(audio, str):
        audio = faster_whisper.decode_audio(audio)
    try:
        import mlx_whisper
    except ImportError:
        mlx_whisper = None
    model = voice_model(bool(mlx_whisper))
    try:
        if mlx_whisper:
            # ponytail: mlx loads and transcribes in one call, so a transcription error also reads as a missing model
            r = mlx_whisper.transcribe(audio, path_or_hf_repo=model, language=lang)
            return [[s["start"], s["text"].strip()] for s in r["segments"]]
        if not cpu_model or cpu_model[0] != model:
            cpu_model = (model, faster_whisper.WhisperModel(model, device="cpu", compute_type="int8"))
    except Exception as e:
        raise NoDictation(f"dictation model {model} not available: {e}")
    segments, _ = cpu_model[1].transcribe(audio, language=lang)
    return [[s.start, s.text.strip()] for s in segments]


def transcribe(raw, lang=None):
    """float32 mono at 16 kHz, as the browser sends it. lang None = auto-detect."""
    try:
        import numpy   # in here: the rest of the server doesn't need it
    except ImportError:
        raise NoDictation("dictation engine missing, start with npm run app")
    with voice_lock:   # ponytail: one transcription at a time, there is a single user
        segments = whisper(numpy.frombuffer(raw, dtype="<f4"), lang)
    # segments [start_s, text]: live dictation pins the old ones and trims the audio there
    return {"text": " ".join(t for _, t in segments).strip(), "segments": segments}


SETTINGS = {"profile": "online", "theme": "", "font": "mono", "voice_model": ""}
PROFILES = ("online", "offline")


def read_settings():
    """settings.json at the repo root. Missing file or missing keys = defaults."""
    file = ROOT / "settings.json"
    saved = json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}
    return {k: saved.get(k, v) for k, v in SETTINGS.items()}


def save_settings(data):
    """Merges the known keys into settings.json. Returns the full settings."""
    settings = read_settings()
    settings.update({k: data[k] for k in SETTINGS if k in data})
    if settings["profile"] not in PROFILES:
        raise ValueError("unknown profile: " + str(settings["profile"]))
    if not all(isinstance(v, str) for v in settings.values()):
        raise ValueError("settings values must be strings")
    (ROOT / "settings.json").write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return settings


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
    return path.relative_to(ROOT).as_posix()


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
                return self.respond(200, read_settings())
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
    if sys.argv[1:2] == ["--transcribe"]:
        print(" ".join(t for _, t in whisper(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)).strip())
        sys.exit(0)
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
