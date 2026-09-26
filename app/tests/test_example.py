#!/usr/bin/env python3
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app" / "server"))
from text import html_to_md, md_to_html, slug

T = ROOT / "topics" / "example"
TYPES = {"book", "certification", "documentation", "course", "practice"}
Q_TYPES = {"multiple_choice", "open", "oral", "practical"}
KINDS = {"reading", "teaching", "summary", "cards", "practice", "exam", "quiz", "feedback"}
BY = {"app", "agent", "hook", "idle"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}(-\d+)?$")
AT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")


def frontmatter(path):
    m = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    assert m, f"{path}: no frontmatter"
    return {k.strip(): v.strip() for k, v in
            (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l and not l.startswith(" "))}


topic = json.loads((T / "topic.json").read_text(encoding="utf-8"))
for k in ("title", "subtitle", "reason", "end_date"):
    assert isinstance(topic[k], str), k
assert topic["type"] in TYPES
assert isinstance(topic["order"], int)
assert isinstance(topic["goals"], list) and 1 <= len(topic["goals"]) <= 3
assert set(topic["language"]) == {"source", "notes", "exams"}
assert set(topic["routine"]) == {"cadence", "session"}
assert topic["sources_mode"] in {"web", "local", "both"}
for link in topic["links"]:
    assert isinstance(link["title"], str) and (("url" in link) != ("path" in link)), link
    assert "url" not in link or link["url"].startswith(("http://", "https://")), link

for note in (T / "notes").glob("*.md"):
    md = note.read_text(encoding="utf-8")
    h1s = re.findall(r"^# (.+)$", md, re.M)
    assert len(h1s) == 1, note
    assert re.fullmatch(r"\d{2}-" + re.escape(slug(h1s[0])) + r"\.md", note.name), note
    assert html_to_md(md_to_html(md)) == md, f"{note} changes on save"

for exam_file in (T / "exams").glob("*/exam.json"):
    folder = exam_file.parent
    exam = json.loads(exam_file.read_text(encoding="utf-8"))
    qs = exam["questions"]
    assert isinstance(exam["title"], str) and qs, exam_file
    quiz = exam.get("kind") == "quiz"
    assert quiz == (folder.name == "quiz"), exam_file
    for q in qs:
        t = q.get("type", "multiple_choice")
        assert t in Q_TYPES and q["q"], q
        if t == "multiple_choice":
            assert len(q["options"]) == 4 and type(q["answer"]) is int and 0 <= q["answer"] < 4 and q["explanation"], q
        else:
            assert 3 <= len(q["rubric"]) <= 5 and "answer" not in q, q
        if quiz:
            assert isinstance(q["thread"], str) and q["level"] in range(1, 6), q
    attempts = folder / "attempts"
    for a in attempts.glob("*.json"):
        assert DATE.match(a.stem), a
        data = json.loads(a.read_text(encoding="utf-8"))
        assert data["exam"] == folder.name, a
        mode = data.get("mode")
        assert mode in (None, "chat"), a
        seen = set()
        for ans in data["answers"]:
            i = ans["i"]
            assert type(i) is int and 0 <= i < len(qs) and i not in seen, (a, i)
            seen.add(i)
            assert ans["type"] == qs[i].get("type", "multiple_choice"), (a, i)
            if ans["type"] == "multiple_choice":
                assert ans["chosen"] in range(4), (a, i)
            else:
                assert "text" in ans or "audio" in ans, (a, i)
            if "audio" in ans:
                assert (attempts / ans["audio"]).is_file(), (a, i)

for fb in T.glob("*/*/attempts/*.feedback.md"):
    date = fb.name[:-len(".feedback.md")]
    assert DATE.match(date), fb
    assert [p for p in fb.parent.glob(date + ".*") if p != fb], f"{fb}: no attempt"

for prompt in (T / "exercises").glob("*/prompt.md"):
    head = prompt.read_text(encoding="utf-8")
    assert re.search(r"\*\*Format:\*\* (apply|build|critique|teach) · \*\*Unit:\*\* \d{2} · \*\*Rests on:\*\* .+ › .+", head), prompt
    for a in (prompt.parent / "attempts").glob("*"):
        assert DATE.match(a.name.split(".")[0]), a

state, kinds_seen = {}, set()
for n, line in enumerate((T / "progress" / "sessions.jsonl").read_text(encoding="utf-8").splitlines(), 1):
    e = json.loads(line)
    assert DATE.match(e["id"]) and AT.match(e["at"]) and e["by"] in BY, n
    ev, s = e["event"], state.get(e["id"])
    if ev == "start":
        assert s is None and e["at"].replace(":", "") == e["id"], n
        assert all(v != "open" for v in state.values()), f"line {n}: two open sessions"
        state[e["id"]] = "open"
    elif ev == "activity":
        assert s == "open" and e["kind"] in KINDS and e["detail"], n
        kinds_seen.add((e["by"], e["kind"]))
    elif ev == "end":
        assert s == "open", f"line {n}: end without open start"
        assert isinstance(e.get("outputs", []), list), n
        state[e["id"]] = "closed" if e["by"] in ("hook", "idle", "app") else "validated"
    else:
        assert ev == "correct" and e["by"] == "agent" and s == "closed", n
        assert AT.match(e["end_at"]) and isinstance(e["outputs"], list) and e["note"], n
        state[e["id"]] = "validated"
assert state and all(v == "validated" for v in state.values()), state
assert any(by == "app" for by, _ in kinds_seen), "no app activity"

wiki = T / "wiki"
index = (wiki / "index.md").read_text(encoding="utf-8")
pages = [p for p in wiki.rglob("*.md") if p.name not in ("index.md", "log.md")]
assert pages
for p in pages:
    meta = frontmatter(p)
    assert meta.get("type") in ("Concept", "Source"), p
    assert meta.get("title") and meta.get("description"), p
    if meta["type"] == "Concept":
        assert "depends_on" in meta, p
        for sid in re.findall(r"[\w:-]+", meta.get("studied", "").strip("[]")):
            assert sid in state, f"{p}: studied in unknown session {sid}"
    assert f"]({p.relative_to(wiki).as_posix()})" in index, f"{p} missing from index"

cards = json.loads((T / "cards" / "cards.json").read_text(encoding="utf-8"))
ids = [c["id"] for c in cards]
assert ids and len(ids) == len(set(ids)), "card ids not unique"
for c in cards:
    assert c["id"] == slug(c["id"]), c
    assert all(isinstance(c[k], str) and c[k].strip() for k in ("front", "back", "note")), c
    assert " › " in c["note"], c
    assert c.get("by", "user") == "user", c
    assert isinstance(c.get("flagged", False), bool), c
for n, line in enumerate((T / "cards" / "reviews.jsonl").read_text(encoding="utf-8").splitlines(), 1):
    r = json.loads(line)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", r["at"]), n
    assert r["id"] in ids and r["recall"] in ("again", "good"), n

log = (T / "progress" / "log.md").read_text(encoding="utf-8")
for section in ("Reading", "Exams", "Exercises", "Quizzes"):
    assert f"\n## {section}\n" in log, section

print("ok")
