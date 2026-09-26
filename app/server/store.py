import base64, datetime, hashlib, json, mimetypes, os, pathlib, re, time, urllib.parse

import text

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOPICS = ROOT / "topics"
BODY_LIMIT = 20 * 1024 * 1024   # ponytail: one flat cap for every POST, single local user


class NotFound(ValueError):
    pass


class Conflict(ValueError):
    def __init__(self, message, **extra):
        super().__init__(message)
        self.extra = extra


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_bytes(path, data):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def write_json(path, data):
    write_bytes(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode())


def now(fmt="%Y-%m-%dT%H:%M"):
    return datetime.datetime.now().strftime(fmt)


AUTO, ONLINE, OFFLINE = PROFILES = ("auto", "online", "offline")
SETTINGS = {"profile": AUTO, "theme": "", "theme_seed": "", "ui_font": "mono", "font": "mono",
            "voice_model": "", "dictation_key": "ctrl+m"}
SETTING_RULES = {
    "profile": (lambda v: v in PROFILES, "unknown profile"),
    "theme": (lambda v: v in ("", "sumi", "kami", "seed"), "theme must be '', sumi, kami or seed"),
    "theme_seed": (lambda v: v == "" or re.fullmatch(r"#[0-9a-fA-F]{6}", v), "theme_seed must be #rrggbb"),
    "dictation_key": (lambda v: re.fullmatch(r"((ctrl|alt|shift|meta)\+)+[a-z0-9]", v), "dictation_key must look like ctrl+m"),
}


def settings_file():
    return ROOT / "settings.json"


def read_settings():
    saved = read_json(settings_file())
    return {k: saved.get(k, v) for k, v in SETTINGS.items()}


def save_settings(data):
    incoming = {k: data[k] for k in SETTINGS if k in data}
    for k, v in incoming.items():
        if not isinstance(v, str):
            raise ValueError(f"setting {k} must be a string")
        ok, message = SETTING_RULES.get(k, (lambda v: True, ""))
        if not ok(v):
            raise ValueError(f"{message}: {v}")
    if "voice_model" in incoming:
        import voice
        voice.check_voice_model(incoming["voice_model"])
    settings = {**read_settings(), **incoming}
    write_json(settings_file(), settings)
    return settings


FONT_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*\.(woff2|ttf|otf)")
FONT_MAGIC = (b"wOF2", b"OTTO", b"\0\1\0\0", b"true")


def fonts_dir():
    return ROOT / "fonts"


def font_name(upload):
    stem, dot, ext = upload.rpartition(".")
    return re.sub(r"\s+", "-", stem.strip().lower()) + dot + ext


def list_fonts():
    d = fonts_dir()
    return sorted(f.name for f in d.iterdir() if f.is_file() and FONT_NAME.fullmatch(f.name)) if d.is_dir() else []


def fonts_css():
    return "\n".join(f'@font-face {{ font-family: "{f}"; src: url("/fonts/{f}"); }}\n'
                     f':root[data-font="{f}"] {{ --reading-font: "{f}", var(--code); }}\n'
                     f':root[data-ui-font="{f}"] {{ --mono: "{f}", var(--code); }}' for f in list_fonts())


def save_font(upload, raw):
    name = font_name(upload)
    if not FONT_NAME.fullmatch(name):
        raise ValueError("font name not allowed (a .woff2, .ttf or .otf file name, no folders): " + upload)
    if len(raw) > BODY_LIMIT:
        raise ValueError("font too large")
    if not raw.startswith(FONT_MAGIC):
        raise ValueError("not a font file: " + upload)
    if (fonts_dir() / name).exists():
        raise Conflict(f"a font named {name} already exists: rename the file or delete fonts/{name}")
    fonts_dir().mkdir(exist_ok=True)
    write_bytes(fonts_dir() / name, raw)
    return {"fonts": list_fonts()}


def plain_name(name):
    return bool(name) and name == pathlib.PurePath(name).name and not name.startswith(".") and "\\" not in name


def folder(slug):
    if not plain_name(slug) or not (TOPICS / slug).is_dir():
        raise NotFound("no such topic: " + slug)
    return TOPICS / slug


def topic_dirs():
    return [d for d in TOPICS.glob("*") if d.is_dir() and not d.name.startswith(".")]


def meta(d):
    saved = read_json(d / "topic.json")
    title = d.name if " " in d.name else d.name.replace("-", " ").capitalize()
    try:
        order = int(saved.get("order", 999))
    except (TypeError, ValueError):
        order = 999
    return {"title": saved.get("title") or title,
            "subtitle": saved.get("subtitle", ""),
            "type": saved.get("type", "book"),
            "order": order,
            "links": saved.get("links", []),
            "language": saved.get("language", {})}


def topic_url(d, *parts):
    return "/" + "/".join(urllib.parse.quote(p) for p in ("topics", d.name) + parts)


def resources(d):
    res = d / "resources"
    if not res.is_dir():
        return []
    return [{"name": f.name, "path": topic_url(d, "resources", f.name), "kb": round(f.stat().st_size / 1024)}
            for f in sorted(res.iterdir()) if f.is_file() and not f.name.startswith(".")]


RESOURCE_NAME = re.compile(r"[\w .()-]+\.\w+")


def save_resource(slug, name, raw):
    d = folder(slug)
    if not RESOURCE_NAME.fullmatch(name or "") or not plain_name(name):
        raise ValueError("resource name not allowed: " + str(name))
    if len(raw) > BODY_LIMIT:
        raise ValueError("resource too large")
    dest = d / "resources" / name
    if dest.exists():
        raise Conflict(f"a resource named {name} already exists")
    dest.parent.mkdir(exist_ok=True)
    write_bytes(dest, raw)
    log_activity(slug, "reading", "resource " + name)
    return {"ok": True, "name": name, "url": topic_url(d, "resources", name)}


def sort_topics(items):
    return sorted(items, key=lambda l: (l["order"], text.slug(l["title"])))


IMG_TYPES = {"png": ".png", "jpeg": ".jpg", "jpg": ".jpg", "gif": ".gif", "webp": ".webp", "avif": ".avif"}
IMG_UPLOAD = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp"}
IMG_NAME = re.compile(r"^[0-9a-f]{16}\.[a-z]+$")
IMG_GRACE = 600   # ponytail: unreferenced images younger than 10 min survive gc, so an upload racing a stale autosave isn't lost


def img_prefix(slug):
    return f'src="/topics/{urllib.parse.quote(slug)}/notes/img/'


def to_url(html, slug):
    return html.replace('src="img/', img_prefix(slug))


def to_path(html, slug):
    return html.replace(img_prefix(slug), 'src="img/')


def store_image(dest, raw, ext):
    name = hashlib.sha1(raw).hexdigest()[:16] + ext
    dest.mkdir(parents=True, exist_ok=True)
    if not (dest / name).exists():
        write_bytes(dest / name, raw)
    return name


def save_image(slug, mime, raw):
    ext = IMG_UPLOAD.get(mime.split(";")[0].strip().lower())
    if not ext:
        raise ValueError("image type not allowed: " + mime)
    if not raw:
        raise ValueError("empty image")
    name = store_image(folder(slug) / "notes" / "img", raw, ext)
    return {"src": f"/topics/{urllib.parse.quote(slug)}/notes/img/{name}"}


def extract_images(html, dest):
    decoded = [(m.group(0), base64.b64decode(m.group(2), validate=True), IMG_TYPES[m.group(1)])
               for m in re.finditer(r'src="data:image/(png|jpeg|jpg|gif|webp|avif);base64,([^"]+)"', html)]
    for whole, raw, ext in decoded:
        html = html.replace(whole, f'src="img/{store_image(dest, raw, ext)}"')
    return html


def gc_images(img, used):
    if not img.is_dir():
        return
    for f in img.iterdir():
        if f.is_file() and f.name not in used and IMG_NAME.match(f.name) and time.time() - f.stat().st_mtime > IMG_GRACE:
            f.unlink()


def section_key(f):
    m = re.match(r"\d+", f.name)
    return (int(m.group()) if m else float("inf"), f.name)


def sections(d):
    return sorted((d / "notes").glob("*.md"), key=section_key)


def stamp(d):
    files = [(f.name, f.stat().st_mtime_ns, f.stat().st_size) for f in sections(d)]
    return hashlib.sha1(repr(files).encode()).hexdigest()[:16]


def headings(d):
    return [text.plain(l[2:]) for f in sections(d)
            for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("# ")]


def topics():
    return sort_topics([{"slug": d.name, **meta(d), "sections": len(sections(d)),
                         "resources": len(resources(d)), "index": headings(d)} for d in topic_dirs()])


def read_topic(slug):
    d = folder(slug)
    parts = [text.md_to_html(f.read_text(encoding="utf-8")) for f in sections(d)]
    return {"slug": slug, **meta(d), "resources": resources(d),
            "html": to_url("\n".join(parts), slug), "stamp": stamp(d)}


def check_links(links):
    if not isinstance(links, list):
        raise ValueError("links must be a list")
    for l in links:
        if not isinstance(l, dict) or not isinstance(l.get("title"), str):
            raise ValueError("each link needs a title")
        url, path = l.get("url"), l.get("path")
        if isinstance(url, str) and re.match(r"https?://", url) and path is None:
            continue
        if isinstance(path, str) and path and url is None:
            continue
        raise ValueError("a link needs an http(s) url or a path: " + json.dumps(l, ensure_ascii=False))
    return links


def topic_meta(data):
    fields = {k: data[k] for k in ("title", "subtitle") if k in data}
    if not all(isinstance(v, str) for v in fields.values()):
        raise ValueError("title and subtitle must be strings")
    if "links" in data:
        fields["links"] = check_links(data["links"])
    return fields


def write_sections(notes, html):
    written, changed = [], []
    for i, (title, chunk) in enumerate(text.split_by_h1(html), 1):
        name, md = f"{i:02d}-{text.slug(title)}.md", text.html_to_md(chunk).encode()
        if not (notes / name).is_file() or (notes / name).read_bytes() != md:
            write_bytes(notes / name, md)
            changed.append(name)
        written.append(name)
    for old in notes.glob("*.md"):
        if old.name not in written:
            old.unlink()
    return changed


def save_topic(slug, data):
    d = folder(slug)
    fields = topic_meta(data)
    html = data.get("html")
    if html is not None:
        if not isinstance(html, str):
            raise ValueError("html must be a string")
        if data.get("stamp") != stamp(d):
            raise Conflict("notes changed on disk, reload", stamp=stamp(d))
        html = extract_images(to_path(html, slug), d / "notes" / "img")
    old_links = meta(d)["links"]
    if fields:
        write_json(d / "topic.json", {**read_json(d / "topic.json"), **fields})
    for link in fields.get("links", []):
        if link not in old_links:
            log_activity(slug, "reading", "link " + link["title"])
    if html is not None:
        (d / "notes").mkdir(exist_ok=True)
        changed = write_sections(d / "notes", html)
        gc_images(d / "notes" / "img", set(re.findall(r'src="img/([^"]+)"', html)))
        if changed:
            log_activity(slug, "reading", ", ".join("notes/" + n for n in changed), every=10)
    return {"ok": True, "sections": [f.name for f in sections(d)], "stamp": stamp(d)}


def source_file(slug, i):
    links = meta(folder(slug))["links"]
    try:
        path = links[int(i)].get("path") if int(i) >= 0 else None
    except (IndexError, AttributeError, TypeError, ValueError):
        path = None
    if not isinstance(path, str):
        raise NotFound("no such source")
    f = pathlib.Path(os.path.expanduser(path))
    if not f.is_file():
        raise NotFound("source file not found: " + str(path))
    return f, mimetypes.guess_type(f.name)[0] or "application/octet-stream"


def exam_index():
    out = [{"slug": d.name, **meta(d),
            "exams": [{"path": f"topics/{d.name}/exams/{f.parent.name}/exam.json",
                       "title": read_json(f).get("title", f.parent.name)}
                      for f in sorted((d / "exams").glob("*/exam.json"))]}
           for d in topic_dirs()]
    return {"topics": sort_topics(out)}


def exam_folder(d, exam):
    c = d / "exams" / str(exam)
    if not plain_name(str(exam)) or not (c / "exam.json").is_file():
        raise NotFound("no such exam: " + str(exam))
    return c


AUDIO_EXT = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "mp4",
             "audio/wav": "wav", "audio/x-wav": "wav"}


def audio_ext(mime):
    ext = AUDIO_EXT.get(str(mime).split(";")[0].strip().lower())
    if not ext:
        raise ValueError("audio type not allowed: " + str(mime))
    return ext


def check_answers(answers, questions):
    if not isinstance(answers, list) or not all(isinstance(a, dict) for a in answers):
        raise ValueError("answers must be a list of objects")
    seen = set()
    for a in answers:
        i = a.get("i")
        if type(i) is not int or not 0 <= i < len(questions) or i in seen:
            raise ValueError(f"bad question index: {i!r}")
        seen.add(i)
        a["type"] = questions[i].get("type", "multiple_choice")
    return sorted(answers, key=lambda a: a["i"])


def free_stem(attempts, date):
    stem, n = date, 1
    while (attempts / (stem + ".json")).exists():
        n += 1
        stem = f"{date}-{n}"
    return stem


def save_attempt(slug, exam, answers):
    c = exam_folder(folder(slug), exam)
    answers = check_answers(answers, read_json(c / "exam.json").get("questions", []))
    audio = {}
    for a in answers:
        clip, mime = a.pop("audio", None), a.pop("mime", "")
        if a["type"] == "oral" and clip is not None:
            audio[a["i"]] = (audio_ext(mime), base64.b64decode(clip, validate=True))
    attempts = c / "attempts"
    attempts.mkdir(exist_ok=True)
    stem = free_stem(attempts, now("%Y-%m-%dT%H%M"))
    for a in answers:
        if a["i"] in audio:
            ext, raw = audio[a["i"]]
            a["audio"] = f"{stem}-p{a['i']}.{ext}"
            write_bytes(attempts / a["audio"], raw)
    path = attempts / (stem + ".json")
    write_json(path, {"exam": exam, "answers": answers})
    log_activity(slug, "quiz" if read_json(c / "exam.json").get("kind") == "quiz" else "exam", "exams/" + exam)
    return "topics/" + path.relative_to(TOPICS).as_posix()


def read_jsonl(f):
    try:
        lines = f.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for l in lines:
        try:
            rec = json.loads(l)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def append_jsonl(f, records):
    f.parent.mkdir(exist_ok=True)
    old = f.read_bytes() if f.is_file() else b""
    head = "\n" if old and not old.endswith(b"\n") else ""
    with f.open("a", encoding="utf-8") as out:
        out.write(head + "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


IDLE_MIN = 30


def sessions_file(d):
    return d / "progress" / "sessions.jsonl"


def minutes(a, b):
    return (datetime.datetime.fromisoformat(b) - datetime.datetime.fromisoformat(a)).total_seconds() / 60


def merge_sessions(records):
    out = {}
    for r in records:
        sid, ev, at = r.get("id"), r.get("event"), r.get("at")
        try:
            datetime.datetime.fromisoformat(at)
        except (TypeError, ValueError):
            continue
        if ev == "start" and sid not in out:
            out[sid] = {"id": sid, "start": at, "by": r.get("by"), "activities": [], "last": at,
                        "end": None, "end_by": None, "outputs": [], "note": "", "corrected": False}
        s = out.get(sid)
        if s is None:
            continue
        if ev == "activity":
            s["activities"].append({k: r.get(k) for k in ("at", "kind", "by", "detail")})
            s["last"] = max(s["last"], at)
        elif ev == "end":
            s.update(end=at, end_by=r.get("by") or r.get("closed_by"), outputs=r.get("outputs", []), note=r.get("note", ""))
        elif ev == "correct":
            s.update(end=r.get("end_at", s["end"]), outputs=r.get("outputs", s["outputs"]),
                     note=r.get("note", s["note"]), corrected=True)
    for s in out.values():
        s["open"] = s["end"] is None
    return list(out.values())


def sessions(slug):
    return merge_sessions(read_jsonl(sessions_file(folder(slug))))


def open_session(d):
    return next((s for s in reversed(merge_sessions(read_jsonl(sessions_file(d)))) if s["open"]), None)


def end_session(d, s, by, at):
    append_jsonl(sessions_file(d), [{"id": s["id"], "event": "end", "at": at, "by": by}])


def live_session(d, at):
    s = open_session(d)
    if s and minutes(s["last"], at) > IDLE_MIN:
        end_session(d, s, "idle", s["last"])
        return None
    return s


def start_session(d, by, at):
    ids = {s["id"] for s in merge_sessions(read_jsonl(sessions_file(d)))}
    base = sid = at.replace(":", "")
    n = 1
    while sid in ids:
        n += 1
        sid = f"{base}-{n}"
    append_jsonl(sessions_file(d), [{"id": sid, "event": "start", "at": at, "by": by}])
    return sid


def log_activity(slug, kind, detail, every=0):
    d, at = folder(slug), now()
    s = live_session(d, at)
    if s and every and any(a["kind"] == kind and minutes(a["at"], at) < every for a in s["activities"]):
        return s["id"]
    sid = s["id"] if s else start_session(d, "app", at)
    append_jsonl(sessions_file(d), [{"id": sid, "event": "activity", "at": at, "kind": kind, "by": "app", "detail": detail}])
    return sid


def session_state(slug):
    s = open_session(folder(slug))
    if not s or minutes(s["last"], now()) > IDLE_MIN:
        return {"open": False, "id": None, "started": None, "last": None}
    return {"open": True, "id": s["id"], "started": s["start"], "last": s["last"]}


def session_action(slug, action):
    d, at = folder(slug), now()
    s = live_session(d, at)
    if action == "start" and not s:
        start_session(d, "app", at)
    elif action == "stop" and s:
        end_session(d, s, "app", at)
    elif action not in ("start", "stop"):
        raise ValueError("action must be start or stop")
    return session_state(slug)


def sweep_sessions(close=False):
    found, at = [], now()
    for d in sorted(topic_dirs()):
        before, live = open_session(d), live_session(d, at)
        if before and not live:
            found.append((d.name, before, "idle"))
        if live and close:
            end_session(d, live, "hook", at)
        if live:
            found.append((d.name, live, "hook" if close else "open"))
    return found


INTERVALS = (0, 1, 3, 7)
RECALLS = ("again", "good")


def schedule(recalls, last, at):
    streak = 0
    for r in recalls:
        streak = streak + 1 if r == "good" else 0
    box = min(streak, 3)
    if last is None:
        return box, True
    due_at = datetime.datetime.fromisoformat(last) + datetime.timedelta(days=INTERVALS[box])
    return box, datetime.datetime.fromisoformat(at) >= due_at


def read_cards(d):
    try:
        data = json.loads((d / "cards" / "cards.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [c for c in data if isinstance(c, dict) and isinstance(c.get("id"), str)] if isinstance(data, list) else []


def deck(d, at=None):
    at = at or now()
    history = {}
    for r in read_jsonl(d / "cards" / "reviews.jsonl"):
        if r.get("recall") in RECALLS and isinstance(r.get("at"), str):
            history.setdefault(r.get("id"), []).append(r)
    out = []
    for c in read_cards(d):
        h = history.get(c["id"], [])
        last = h[-1]["at"] if h else None
        try:
            box, due = schedule([r["recall"] for r in h], last, at)
        except ValueError:
            box, due = 0, True
        out.append({**{k: c.get(k, "") for k in ("id", "front", "back", "note")}, "flagged": c.get("flagged") is True,
                    "box": box, "due": due, "last": last})
    return sorted(out, key=lambda c: (not c["due"], c["box"]))


def cards_index():
    out = []
    for d in topic_dirs():
        cards = deck(d)
        out.append({"slug": d.name, **{k: v for k, v in meta(d).items() if k in ("title", "subtitle", "order")},
                    "cards": len(cards), "due": sum(c["due"] for c in cards), "flagged": sum(c["flagged"] for c in cards)})
    return {"topics": sort_topics(out)}


def read_deck(slug):
    d = folder(slug)
    return {"slug": slug, "title": meta(d)["title"], "cards": deck(d)}


def write_cards(d, cards):
    (d / "cards").mkdir(exist_ok=True)
    write_json(d / "cards" / "cards.json", cards)


def upsert_card(slug, card):
    d = folder(slug)
    if not isinstance(card, dict):
        raise ValueError("upsert must be an object")
    fields = {k: card.get(k, "") for k in ("front", "back", "note")}
    if not all(isinstance(v, str) for v in fields.values()):
        raise ValueError("front, back and note must be strings")
    fields = {k: v.strip() for k, v in fields.items()}
    if not fields["front"] or not fields["back"]:
        raise ValueError("front and back cannot be empty")
    cards = read_cards(d)
    if "id" in card:
        old = next((c for c in cards if c["id"] == card["id"]), None)
        if old is None:
            raise NotFound(f"no such card: {card['id']!r}")
        old.update(fields)
    else:
        ids, base = {c["id"] for c in cards}, text.slug(fields["front"], "card")[:48].strip("-")
        new_id, n = base, 1
        while new_id in ids:
            n += 1
            new_id = f"{base}-{n}"
        cards.append({"id": new_id, **fields, "by": "user"})
    write_cards(d, cards)
    return read_deck(slug)


def flag_card(slug, flag):
    d = folder(slug)
    if not isinstance(flag, dict) or not isinstance(flag.get("flagged"), bool):
        raise ValueError("flag must be {id, flagged: bool}")
    cards = read_cards(d)
    card = next((c for c in cards if c["id"] == flag.get("id")), None)
    if card is None:
        raise NotFound(f"no such card: {flag.get('id')!r}")
    card["flagged"] = flag["flagged"]
    write_cards(d, cards)
    return read_deck(slug)


def delete_card(slug, card_id):
    d = folder(slug)
    cards = read_cards(d)
    kept = [c for c in cards if c["id"] != card_id]
    if len(kept) == len(cards):
        raise NotFound(f"no such card: {card_id!r}")
    write_cards(d, kept)
    return read_deck(slug)


def save_reviews(slug, reviews):
    d = folder(slug)
    ids = {c["id"] for c in read_cards(d)}
    if not isinstance(reviews, list) or not all(isinstance(r, dict) for r in reviews):
        raise ValueError("reviews must be a list of objects")
    for r in reviews:
        if r.get("id") not in ids:
            raise ValueError(f"no such card: {r.get('id')!r}")
        if r.get("recall") not in RECALLS:
            raise ValueError("recall must be again or good")
    at = now()
    append_jsonl(d / "cards" / "reviews.jsonl", [{"at": at, "id": r["id"], "recall": r["recall"]} for r in reviews])
    log_activity(slug, "cards", f"{len(reviews)} reviewed, {sum(r['recall'] == 'again' for r in reviews)} again")
    return {"ok": True, "due": sum(c["due"] for c in deck(d))}
