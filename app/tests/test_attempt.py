#!/usr/bin/env python3
import base64, json, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import store


def with_test_topic(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()   # same symlink-resolved path folder() uses
        real_root, real_topics = store.ROOT, store.TOPICS
        store.ROOT, store.TOPICS = tmp, tmp / "topics"
        d = store.TOPICS / "demo" / "exams" / "ch-01"
        d.mkdir(parents=True)
        (d / "exam.json").write_text(json.dumps({"title": "demo", "questions": [
            {"q": "a", "options": ["x", "y"], "answer": 1}, {"type": "open", "q": "b"}, {"type": "oral", "q": "c"}]}))
        try:
            f()
        finally:
            store.ROOT, store.TOPICS = real_root, real_topics
            shutil.rmtree(tmp)
    return wrapped


def expect_rejection(f):
    try:
        f()
    except ValueError:
        return
    raise AssertionError("should have rejected: " + f.__name__)


@with_test_topic
def test_writes_attempt():
    path = store.save_attempt("demo", "ch-01", [{"i": 0, "type": "multiple_choice", "chosen": 1}])
    file = store.ROOT / path
    assert file.is_file(), "did not write the file"
    data = json.loads(file.read_text())
    assert data == {"exam": "ch-01", "answers": [{"i": 0, "type": "multiple_choice", "chosen": 1}]}


@with_test_topic
def test_saves_oral_audio():
    raw = b"\x00\x01fake-audio"
    path = store.save_attempt("demo", "ch-01", [
        {"i": 2, "type": "oral", "audio": base64.b64encode(raw).decode(), "mime": "audio/webm;codecs=opus"}])
    data = json.loads((store.ROOT / path).read_text())
    name = data["answers"][0]["audio"]
    assert name == path.split("/")[-1].replace(".json", "-p2.webm")
    assert (store.ROOT / path).parent.joinpath(name).read_bytes() == raw
    assert "mime" not in data["answers"][0], "the mime must not stay in the json"


def test_empty_topics():
    real = store.TOPICS
    store.TOPICS = pathlib.Path(tempfile.mkdtemp()).resolve() / "missing"
    try:
        assert store.topics() == [] and store.exam_index() == {"topics": []}
    finally:
        store.TOPICS = real


@with_test_topic
def test_answers_follow_exam_json():
    path = store.save_attempt("demo", "ch-01", [
        {"i": 1, "type": "multiple_choice", "text": "shuffled first"}, {"i": 0, "chosen": 1}])
    data = json.loads((store.ROOT / path).read_text())
    assert [a["i"] for a in data["answers"]] == [0, 1], "answers must be in exam.json order"
    assert [a["type"] for a in data["answers"]] == ["multiple_choice", "open"], "type comes from exam.json"


@with_test_topic
def test_rejects_bad_index():
    for i in (3, -1, "0", None):
        expect_rejection(lambda: store.save_attempt("demo", "ch-01", [{"i": i}]))
    expect_rejection(lambda: store.save_attempt("demo", "ch-01", [{"i": 0}, {"i": 0}]))


@with_test_topic
def test_rejects_missing_slug():
    expect_rejection(lambda: store.save_attempt("../outside", "ch-01", []))


@with_test_topic
def test_rejects_escaping_exam():
    expect_rejection(lambda: store.save_attempt("demo", "../../outside", []))


@with_test_topic
def test_rejects_missing_exam():
    expect_rejection(lambda: store.save_attempt("demo", "does-not-exist", []))


@with_test_topic
def test_same_minute_gets_a_suffix():
    raw = base64.b64encode(b"clip").decode()
    oral = [{"i": 2, "audio": raw, "mime": "audio/ogg"}]
    p1 = store.save_attempt("demo", "ch-01", [dict(a) for a in oral])
    p2 = store.save_attempt("demo", "ch-01", [dict(a) for a in oral])
    p3 = store.save_attempt("demo", "ch-01", [{"i": 0, "chosen": 1}])
    assert p1 != p2 != p3 and p2.endswith("-2.json") and p3.endswith("-3.json"), (p1, p2, p3)
    audio = json.loads((store.ROOT / p2).read_text())["answers"][0]["audio"]
    assert audio.endswith("-2-p2.ogg") and (store.ROOT / p2).parent.joinpath(audio).is_file()


@with_test_topic
def test_rejected_audio_leaves_no_files():
    ok = {"i": 2, "audio": base64.b64encode(b"x").decode(), "mime": "audio/webm"}
    expect_rejection(lambda: store.save_attempt("demo", "ch-01", [dict(ok, mime="video/mp4")]))
    expect_rejection(lambda: store.save_attempt("demo", "ch-01", [dict(ok, audio="not base64!")]))
    expect_rejection(lambda: store.save_attempt("demo", "ch-01", [dict(ok), {"i": 7}]))
    attempts = store.TOPICS / "demo" / "exams" / "ch-01" / "attempts"
    assert not attempts.exists() or not list(attempts.iterdir()), "no orphan audio"


@with_test_topic
def test_audio_on_a_written_question_is_dropped():
    path = store.save_attempt("demo", "ch-01", [{"i": 1, "text": "t", "audio": "eA==", "mime": "audio/webm"}])
    assert json.loads((store.ROOT / path).read_text())["answers"][0] == {"i": 1, "type": "open", "text": "t"}


MC = {"type": "multiple_choice", "q": "q?", "options": ["a", "b", "c", "d"], "answer": 2, "explanation": "c because"}
OPEN = {"type": "open", "q": "why?", "rubric": ["one", "two", "three"]}


@with_test_topic
def test_exam_standard_and_crud():
    assert store.exam_errors({"title": "t", "questions": [MC, OPEN]}) == []
    bad = [{"title": "", "questions": [MC]}, {"title": "t", "questions": []}, {"title": "t", "questions": [MC], "extra": 1},
           {"title": "t", "questions": [{**MC, "options": ["a", "b", "c"]}]}, {"title": "t", "questions": [{**MC, "answer": 4}]},
           {"title": "t", "questions": [{**MC, "explanation": " "}]}, {"title": "t", "questions": [{**MC, "options": ["a", "a", "c", "d"]}]},
           {"title": "t", "questions": [{**OPEN, "rubric": ["one", "two"]}]}, {"title": "t", "questions": [{**OPEN, "answer": 1}]},
           {"title": "t", "questions": [{**OPEN, "type": "essay"}]}, {"title": "t", "kind": "quiz", "questions": [MC]},
           {"title": "t", "kind": "quiz", "questions": [{**MC, "thread": "Bad Thread", "level": 3}]}]
    for exam in bad:
        assert store.exam_errors(exam), exam
    assert store.exam_errors({"title": "t", "kind": "quiz", "questions": [{**MC, "thread": "methods", "level": 3}]}) == []
    r = store.save_exam("demo", {"create": True, "exam": {"title": "Methods & codes", "questions": [MC]}})
    assert r["name"] == "01-methods-codes", r
    assert store.save_exam("demo", {"create": True, "exam": {"title": "More", "questions": [MC]}})["name"] == "02-more"
    expect_rejection(lambda: store.save_exam("demo", {"create": True, "name": "02-more", "exam": {"title": "x", "questions": [MC]}}))
    store.save_exam("demo", {"name": "01-methods-codes", "exam": {"title": "Renamed", "questions": [OPEN]}})
    store.save_attempt("demo", "01-methods-codes", [{"i": 0, "text": "x"}])
    loose = {"title": "", "questions": [{"type": "multiple_choice", "q": "no answer", "options": ["a", "b"]}, {"type": "open", "q": "", "rubric": []}]}
    store.save_exam("demo", {"name": "01-methods-codes", "exam": loose})
    assert json.loads((store.TOPICS / "demo" / "exams" / "01-methods-codes" / "exam.json").read_text()) == loose, "the app saves what the user wrote"
    for broken in ({"title": "t"}, {"title": "t", "questions": [{"type": "essay"}]}, {"title": "t", "questions": [{"q": "x", "options": "ab"}]}):
        expect_rejection(lambda: store.save_exam("demo", {"name": "01-methods-codes", "exam": broken}))
    expect_rejection(lambda: store.save_exam("demo", {"name": "nope", "exam": {"title": "t", "questions": [MC]}}))
    expect_rejection(lambda: store.delete_exams("demo", ["02-more", "../x"]))
    assert store.delete_exams("demo", ["02-more", "01-methods-codes"])["deleted"] == ["02-more", "01-methods-codes"]
    assert [e["name"] for e in store.exam_index()["topics"][0]["exams"]] == ["ch-01"]


if __name__ == "__main__":
    test_same_minute_gets_a_suffix()
    test_rejected_audio_leaves_no_files()
    test_audio_on_a_written_question_is_dropped()
    test_writes_attempt()
    test_saves_oral_audio()
    test_answers_follow_exam_json()
    test_rejects_bad_index()
    test_rejects_missing_slug()
    test_rejects_escaping_exam()
    test_rejects_missing_exam()
    test_empty_topics()
    test_exam_standard_and_crud()
    print("ok")
