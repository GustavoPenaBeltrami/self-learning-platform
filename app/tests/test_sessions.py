#!/usr/bin/env python3
import contextlib, datetime, io, json, pathlib, shutil, sys, tempfile, threading, http.server

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import server, store
from test_http import call

clock = [datetime.datetime(2026, 9, 26, 10, 0)]
store.now = lambda fmt="%Y-%m-%dT%H:%M": clock[0].strftime(fmt)


def at(hm):
    clock[0] = datetime.datetime(2026, 9, 26, *map(int, hm.split(":")))


def lines(slug):
    return [json.loads(l) for l in (store.TOPICS / slug / "progress" / "sessions.jsonl").read_text().splitlines()]


def cli(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        server.main(["sessions", *args])
    return out.getvalue()


def test_sessions():
    tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
    real = store.ROOT, store.TOPICS
    store.ROOT, store.TOPICS = tmp, tmp / "topics"
    d = store.TOPICS / "a"
    (d / "notes").mkdir(parents=True)
    (d / "notes" / "01-x.md").write_text("# X\n")
    (d / "exams" / "quiz").mkdir(parents=True)
    (d / "exams" / "quiz" / "exam.json").write_text(json.dumps({"kind": "quiz", "questions": [{"type": "open"}]}))
    (d / "cards").mkdir()
    (d / "cards" / "cards.json").write_text(json.dumps([{"id": "c1", "front": "f", "back": "b"}, {"id": "c2", "front": "g", "back": "h"}]))
    (store.TOPICS / "b").mkdir()
    try:
        at("10:10")
        html = store.read_topic("a")["html"]
        stamp = store.save_topic("a", {"html": html.replace("X", "Y"), "stamp": store.read_topic("a")["stamp"]})["stamp"]
        at("10:12")
        stamp = store.save_topic("a", {"html": "<h1>Z</h1>", "stamp": stamp})["stamp"]
        store.save_topic("a", {"html": "<h1>Z</h1>", "stamp": stamp})
        at("10:25")
        store.save_resource("a", "r.pdf", b"%PDF")
        store.save_topic("a", {"links": [{"title": "site", "url": "https://x.dev"}]})
        store.save_topic("a", {"links": [{"title": "site", "url": "https://x.dev"}]})
        store.save_reviews("a", [{"id": "c1", "recall": "again"}, {"id": "c2", "recall": "good"}])
        store.save_attempt("a", "quiz", [{"i": 0, "text": "t"}])
        recs = lines("a")
        assert [r["event"] for r in recs] == ["start", "activity", "activity", "activity", "activity", "activity"], recs
        assert recs[0] == {"id": "2026-09-26T1010", "event": "start", "at": "2026-09-26T10:10", "by": "app"}
        assert [(r["kind"], r["detail"]) for r in recs[1:]] == [
            ("reading", "notes/01-y.md"), ("reading", "resource r.pdf"), ("reading", "link site"),
            ("cards", "2 reviewed, 1 again"), ("quiz", "exams/quiz")], recs
        assert all(r["by"] == "app" and r["id"] == "2026-09-26T1010" for r in recs)

        at("10:50")
        assert store.session_state("a") == {"open": True, "id": "2026-09-26T1010", "started": "2026-09-26T10:10", "last": "2026-09-26T10:25"}
        at("11:00")
        assert not store.session_state("a")["open"], "idle > 30 min reads as closed"
        store.save_resource("a", "s.pdf", b"%PDF")
        recs = lines("a")
        assert recs[-3] == {"id": "2026-09-26T1010", "event": "end", "at": "2026-09-26T10:25", "by": "idle"}
        assert recs[-2]["event"] == "start" and recs[-2]["id"] == "2026-09-26T1100" and recs[-1]["id"] == "2026-09-26T1100"

        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            api = lambda body=None: json.loads(call(port, "POST" if body else "GET", "/api/session/a", body)[2])
            assert api()["open"]
            assert api(b'{"action":"stop"}')["open"] is False
            assert lines("a")[-1] == {"id": "2026-09-26T1100", "event": "end", "at": "2026-09-26T11:00", "by": "app"}
            assert api(b'{"action":"start"}')["id"] == "2026-09-26T1100-2", "same-minute restart gets a fresh id"
            assert api(b'{"action":"start"}')["id"] == "2026-09-26T1100-2", "start is a no-op when one is open"
            assert call(port, "POST", "/api/session/a", b'{"action":"x"}')[0] == 400
            assert call(port, "GET", "/api/session/nope")[0] == 404
        finally:
            srv.shutdown()

        store.append_jsonl(d / "progress" / "sessions.jsonl", [
            {"id": "2026-09-26T1010", "event": "correct", "at": "2026-09-26T18:00", "by": "agent",
             "end_at": "2026-09-26T10:20", "outputs": ["notes/01-y.md"], "note": "fix"}])
        first = store.sessions("a")[0]
        assert first["end"] == "2026-09-26T10:20" and first["outputs"] == ["notes/01-y.md"] and first["corrected"]
        assert [a["kind"] for a in first["activities"]] == ["reading", "reading", "reading", "cards", "quiz"]
        assert [s["open"] for s in store.sessions("a")] == [False, False, True]

        (store.TOPICS / "b" / "progress").mkdir()
        (store.TOPICS / "b" / "progress" / "sessions.jsonl").write_text(
            '{"id":"old","event":"start","at":"2026-09-25T18:10","type":"teaching"}\nnot json')
        at("11:05")
        out = cli()
        assert out == ("a 2026-09-26T1100-2 started 2026-09-26T11:00 last 2026-09-26T11:00 activities -: open\n"
                       "b old started 2026-09-25T18:10 last 2026-09-25T18:10 activities -: closed idle at 2026-09-25T18:10\n"), out
        assert cli("close") == "a 2026-09-26T1100-2 started 2026-09-26T11:00 last 2026-09-26T11:00 activities -: closed by hook\n"
        assert lines("a")[-1] == {"id": "2026-09-26T1100-2", "event": "end", "at": "2026-09-26T11:05", "by": "hook"}
        assert cli() == "" and cli("close") == ""
    finally:
        store.ROOT, store.TOPICS = real
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_sessions()
    print("ok")
