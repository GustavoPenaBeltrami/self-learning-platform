#!/usr/bin/env python3
import http.server, json, pathlib, shutil, sys, tempfile, threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import server, store
from test_attempt import expect_rejection
from test_http import call

PROMPT = "# Exercise — Pick the code\n\n**Format:** build · **Unit:** 02 · **Rests on:** A › B\n\nDo it.\n"


def with_test_topic(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real_root, real_topics = store.ROOT, store.TOPICS
        store.ROOT, store.TOPICS = tmp, tmp / "topics"
        d = store.TOPICS / "demo"
        (d / "exercises" / "pick-code").mkdir(parents=True)
        (d / "exercises" / "pick-code" / "prompt.md").write_text(PROMPT)
        (d / "exercises" / "bare").mkdir()
        (d / "exercises" / "bare" / "prompt.md").write_text("Just text.\n")
        (d / "exams" / "ch-01").mkdir(parents=True)
        (d / "exams" / "ch-01" / "exam.json").write_text(json.dumps({"title": "E", "questions": [{"type": "open", "q": "b"}]}))
        try:
            f()
        finally:
            store.ROOT, store.TOPICS = real_root, real_topics
            shutil.rmtree(tmp)
    return wrapped


def rows():
    return {e["name"]: e for e in store.exercise_index()["topics"][0]["exercises"]}


@with_test_topic
def test_index_parsing():
    ex = rows()
    assert ex["pick-code"] == {"name": "pick-code", "title": "Pick the code", "format": "build", "unit": "02",
                               "prompt": PROMPT, "attempts": 0, "pending": 0}, ex["pick-code"]
    assert (ex["bare"]["title"], ex["bare"]["format"], ex["bare"]["unit"]) == ("bare", "", "")
    assert store.exercise_index()["topics"][0]["slug"] == "demo"


@with_test_topic
def test_save_attempt_and_pending():
    p1 = store.save_exercise_attempt("demo", "pick-code", "four lines")
    p2 = store.save_exercise_attempt("demo", "pick-code", "again")
    assert p1.endswith(".md") and p2.endswith("-2.md") and (store.ROOT / p1).read_text() == "four lines"
    (store.ROOT / p1).with_name(pathlib.Path(p1).stem + ".feedback.md").write_text("graded")
    assert (rows()["pick-code"]["attempts"], rows()["pick-code"]["pending"]) == (2, 1)
    for bad in ("", "  ", None):
        expect_rejection(lambda: store.save_exercise_attempt("demo", "pick-code", bad))
    for name in ("nope", "../pick-code", "Pick-Code"):
        expect_rejection(lambda: store.save_exercise_attempt("demo", name, "x"))
    expect_rejection(lambda: store.save_exercise_attempt("../x", "pick-code", "x"))


@with_test_topic
def test_image_save_and_refs():
    src = store.save_exercise_image("demo", "pick-code", "image/png", b"\x89PNG")["src"]
    name = src.rsplit("/", 1)[1]
    assert src == f"/topics/demo/exercises/pick-code/img/{name}" and (store.TOPICS / "demo/exercises/pick-code/img" / name).is_file()
    expect_rejection(lambda: store.save_exercise_image("demo", "pick-code", "image/svg+xml", b"<svg/>"))
    expect_rejection(lambda: store.save_exercise_image("demo", "pick-code", "image/png", b""))
    p = store.save_exercise_attempt("demo", "pick-code", f"see ![fig](img/{name}) and ![abs]({src})")
    assert (store.ROOT / p).read_text() == f"see ![fig](img/{name}) and ![abs](img/{name})"
    for ref in ("img/0000000000000000.png", "img/../../../topic.json", "img/", f"img/{name}/x"):
        expect_rejection(lambda: store.save_exercise_attempt("demo", "pick-code", f"![x]({ref})"))
    expect_rejection(lambda: store.save_exercise_attempt("demo", "bare", f"![x](img/{name})"))


@with_test_topic
def test_drafts():
    for kind, name in (("exam", "ch-01"), ("exercise", "pick-code")):
        assert store.read_draft("demo", kind, name) == {"data": None}
        saved = store.save_draft("demo", kind, name, {"answers": [1], "left": 30})
        assert store.read_draft("demo", kind, name) == saved and saved["data"] == {"answers": [1], "left": 30}
        store.delete_draft("demo", kind, name)
        assert store.read_draft("demo", kind, name) == {"data": None}
    expect_rejection(lambda: store.save_draft("demo", "exam", "ch-01", [1]))
    expect_rejection(lambda: store.save_draft("demo", "exam", "ch-01", {"x": "a" * store.DRAFT_LIMIT}))
    for kind, name in (("cards", "ch-01"), ("exam", "nope"), ("exam", "../ch-01"), ("exercise", "ch-01")):
        expect_rejection(lambda: store.read_draft("demo", kind, name))

    store.save_draft("demo", "exam", "ch-01", {"a": 1})
    store.save_draft("demo", "exercise", "pick-code", {"a": 1})
    exam = store.exam_index()["topics"][0]["exams"][0]
    assert (exam["attempts"], exam["pending"]) == (0, 0) and rows()["pick-code"]["attempts"] == 0
    store.save_attempt("demo", "ch-01", [{"i": 0, "text": "t"}])
    store.save_exercise_attempt("demo", "pick-code", "done")
    assert store.read_draft("demo", "exam", "ch-01") == {"data": None}
    assert store.read_draft("demo", "exercise", "pick-code") == {"data": None}
    store.save_draft("demo", "exam", "ch-01", {"a": 1})
    assert store.delete_exams("demo", ["ch-01"])["deleted"] == ["ch-01"]


@with_test_topic
def test_http_routes():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        s, _, body = call(port, "GET", "/api/exercises")
        assert s == 200 and json.loads(body)["topics"][0]["exercises"][1]["name"] == "pick-code"
        s, _, body = call(port, "POST", "/api/exercises/demo/pick-code/img", b"\x89PNG", headers={"Content-Type": "image/png"})
        src = json.loads(body)["src"]
        s, h, body = call(port, "GET", src)
        assert s == 200 and body == b"\x89PNG" and "Content-Security-Policy" not in h
        attempt = json.dumps({"attempt": {"exercise": "pick-code", "text": f"![x](img/{src.rsplit('/', 1)[1]})"}}).encode()
        assert call(port, "POST", "/api/exercises/demo", attempt, headers={"Origin": "https://evil.example"})[0] == 403
        s, _, body = call(port, "POST", "/api/exercises/demo", attempt)
        assert s == 200 and json.loads(body)["path"].startswith("topics/demo/exercises/pick-code/attempts/")
        assert call(port, "POST", "/api/exercises/demo", b'{"attempt":{"exercise":"nope","text":"x"}}')[0] == 404
        assert call(port, "POST", "/api/exercises/demo", b'{"attempt":{"exercise":"pick-code","text":"![](img/x.png)"}}')[0] == 400

        url = "/api/draft/demo/exam/ch-01"
        assert json.loads(call(port, "GET", url)[2]) == {"data": None}
        assert call(port, "PUT", url, b'{"data":{"i":1}}', headers={"Origin": "https://evil.example"})[0] == 403
        s, _, body = call(port, "PUT", url, b'{"data":{"i":1}}')
        assert s == 200 and json.loads(body)["data"] == {"i": 1} and "saved" in json.loads(body)
        assert json.loads(call(port, "GET", url)[2])["data"] == {"i": 1}
        assert call(port, "PUT", url, b'{"data":3}')[0] == 400
        assert call(port, "PUT", "/api/draft/demo/cards/ch-01", b'{"data":{}}')[0] == 404
        assert call(port, "DELETE", url)[0] == 200
        assert json.loads(call(port, "GET", url)[2]) == {"data": None}
        assert call(port, "DELETE", "/api/nope")[0] == 404
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    test_index_parsing()
    test_save_attempt_and_pending()
    test_image_save_and_refs()
    test_drafts()
    test_http_routes()
    print("ok")
