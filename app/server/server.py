#!/usr/bin/env python3
import http.server, json, pathlib, posixpath, shutil, sys, threading, urllib.parse, webbrowser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import store, voice

PORT = 8321
STATIC = ("/app/", "/topics/", "/fonts/")
UNSANDBOXED = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".pdf")
REDIRECTS = {"/": "/app/views/notes.html", "/settings": "/app/views/settings.html"}
write_lock = threading.Lock()   # ponytail: one global write lock, single local user; per-topic locks if saves ever queue up


def json_body(raw):
    data = json.loads(raw or b"{}")
    if not isinstance(data, dict):
        raise ValueError("body must be a JSON object")
    return data


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(store.ROOT), **kw)

    def trusted(self):
        port = self.server.server_address[1]
        hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in hosts and (origin is None or origin.split("//", 1)[-1] in hosts)

    def respond(self, code, data):
        self.send_bytes(code, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def send_bytes(self, code, body, kind):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def handle_api(self, route):
        if not self.trusted():
            return self.respond(403, {"error": "untrusted Host or Origin"})
        raw_path, _, query = self.path.partition("?")
        segs = [urllib.parse.unquote(s) for s in raw_path.split("/")[1:]]
        try:
            route("/" + "/".join(segs), segs, urllib.parse.parse_qs(query))
        except voice.NoDictation as e:
            self.respond(503, {"error": str(e), "fallback": True})
        except store.NotFound as e:
            self.respond(404, {"error": str(e)})
        except store.Conflict as e:
            self.respond(409, {"error": str(e), **e.extra})
        except (ValueError, KeyError, TypeError) as e:
            self.respond(400, {"error": str(e)})
        except Exception as e:
            self.respond(500, {"error": f"{type(e).__name__}: {e}"})

    def do_GET(self):
        self.handle_api(self.get)

    def do_POST(self):
        self.handle_api(self.post)

    def do_HEAD(self):
        self.send_error(405)

    def get(self, path, segs, q):
        if path in REDIRECTS:
            self.send_response(302)
            self.send_header("Location", REDIRECTS[path])
            return self.end_headers()
        if segs[0] != "api":
            return self.static(path)
        if path == "/api/settings":
            return self.respond(200, {**store.read_settings(), "active_profile": voice.active_profile()})
        if path == "/api/voice-models":
            return self.respond(200, {k: {"disk": m["disk"], "ram": m["ram"]} for k, m in voice.MODELS.items()})
        if path == "/api/fonts":
            return self.respond(200, {"fonts": store.list_fonts()})
        if path == "/api/fonts.css":
            return self.send_bytes(200, store.fonts_css().encode(), "text/css; charset=utf-8")
        if path == "/api/index":
            return self.respond(200, store.exam_index())
        if path == "/api/cards":
            return self.respond(200, store.cards_index())
        if len(segs) == 3 and segs[1] == "cards":
            return self.respond(200, store.read_deck(segs[2]))
        if path == "/api/topics":
            return self.respond(200, {"topics": store.topics()})
        if path == "/api/source":
            return self.source(q.get("topic", [""])[0], q.get("i", [""])[0])
        if len(segs) == 3 and segs[1] == "topic":
            return self.respond(200, store.read_topic(segs[2]))
        if len(segs) == 3 and segs[1] == "session":
            return self.respond(200, store.session_state(segs[2]))
        raise store.NotFound("no such endpoint: " + path)

    def static(self, path):
        if not posixpath.normpath(path).startswith(STATIC):
            return self.send_error(404)
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)

    def source(self, slug, i):
        f, kind = store.source_file(slug, i)
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(f.stat().st_size))
        if not f.name.lower().endswith(UNSANDBOXED):
            self.send_header("Content-Security-Policy", "sandbox")
        self.end_headers()
        with f.open("rb") as src:
            shutil.copyfileobj(src, self.wfile)

    def body(self):
        length = self.headers.get("Content-Length") or ""
        if not length.isdigit() or int(length) > store.BODY_LIMIT:
            raise ValueError("missing, bad or too large Content-Length")
        return self.rfile.read(int(length))

    def post(self, path, segs, q):
        raw = self.body()
        if path == "/api/voice":
            return self.respond(200, voice.transcribe(raw, q.get("lang", [None])[0]))
        if path == "/api/voice-model/download":
            size = json_body(raw).get("size")
            voice.download_voice_model(size)
            with write_lock:
                return self.respond(200, store.save_settings({"voice_model": size}))
        with write_lock:
            result = self.write(path, segs, q, raw)
        self.respond(200, result)

    def write(self, path, segs, q, raw):
        if path == "/api/settings":
            return store.save_settings(json_body(raw))
        if path == "/api/font":
            return store.save_font(q.get("name", [""])[0], raw)
        if path == "/api/attempt":
            data = json_body(raw)
            return {"path": store.save_attempt(data["slug"], data["exam"], data["answers"])}
        if segs[:2] == ["api", "cards"] and len(segs) == 3:
            data = json_body(raw)
            if "upsert" in data:
                return store.upsert_card(segs[2], data["upsert"])
            if "flag" in data:
                return store.flag_card(segs[2], data["flag"])
            if "delete" in data:
                return store.delete_card(segs[2], data["delete"])
            return store.save_reviews(segs[2], data["reviews"])
        if segs[:2] == ["api", "session"] and len(segs) == 3:
            return store.session_action(segs[2], json_body(raw).get("action"))
        if segs[:2] == ["api", "topic"] and len(segs) == 3:
            return store.save_topic(segs[2], json_body(raw))
        if segs[:2] == ["api", "topic"] and len(segs) == 4 and segs[3] == "img":
            return store.save_image(segs[2], self.headers.get("Content-Type", ""), raw)
        if segs[:2] == ["api", "topic"] and len(segs) == 4 and segs[3] == "resource":
            return store.save_resource(segs[2], q.get("name", [""])[0], raw)
        raise store.NotFound("no such endpoint: " + path)

    def end_headers(self):
        path = posixpath.normpath(urllib.parse.unquote(self.path.split("?")[0]))
        if path.endswith((".html", ".css", ".js")):
            self.send_header("Cache-Control", "no-store")
        if path.startswith("/topics/") and not path.lower().endswith(UNSANDBOXED):
            self.send_header("Content-Security-Policy", "sandbox")
        super().end_headers()

    def log_message(self, *a):
        pass  # ponytail: no console noise; remove the pass to debug


def sessions(args):
    if args not in ([], ["close"]):
        sys.exit("usage: slp sessions [close]")
    for slug, s, how in store.sweep_sessions(close=bool(args)):
        kinds = ",".join(dict.fromkeys(str(a["kind"]) for a in s["activities"])) or "-"
        ended = {"open": "open", "idle": f"closed idle at {s['last']}", "hook": "closed by hook"}[how]
        print(f"{slug} {s['id']} started {s['start']} last {s['last']} activities {kinds}: {ended}")


def serve():
    print(f"Profile: {voice.active_profile()}")
    url = f"http://localhost:{PORT}/app/views/notes.html"
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"A server was already running on {PORT}. Opening {url}")
        webbrowser.open(url)
        return
    print(f"Study app at {url}  (ctrl+c to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


def main(args=None):
    args = sys.argv[1:] if args is None else args
    if args[:1] == ["setup"]:
        print("Setup done:", json.dumps(voice.setup()), "\nStart the app with uv run slp")
    elif args[:1] == ["sessions"]:
        sessions(args[1:])
    elif args[:1] == ["transcribe"] and len(args) in (2, 3):
        print(" ".join(t for _, t in voice.whisper(args[1], args[2] if len(args) > 2 else None)).strip())
    elif args:
        sys.exit("usage: slp [setup | sessions [close] | transcribe <audio> [lang]]")
    else:
        serve()


if __name__ == "__main__":
    main()
