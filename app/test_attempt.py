#!/usr/bin/env python3
"""Self-check of save_attempt() (POST /api/attempt): python3 app/test_attempt.py"""
import base64, json, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import server


def with_test_topic(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()   # same symlink-resolved path folder() uses
        real_root, real_topics = server.ROOT, server.TOPICS
        server.ROOT, server.TOPICS = tmp, tmp / "topics"
        d = server.TOPICS / "demo" / "exams" / "ch-01"
        d.mkdir(parents=True)
        (d / "exam.json").write_text('{"title": "demo", "questions": []}')
        try:
            f()
        finally:
            server.ROOT, server.TOPICS = real_root, real_topics
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
    path = server.save_attempt("demo", "ch-01", [{"i": 0, "type": "multiple_choice", "chosen": 1}])
    file = server.ROOT / path
    assert file.is_file(), "did not write the file"
    data = json.loads(file.read_text())
    assert data == {"exam": "ch-01", "answers": [{"i": 0, "type": "multiple_choice", "chosen": 1}]}


@with_test_topic
def test_saves_oral_audio():
    raw = b"\x00\x01fake-audio"
    path = server.save_attempt("demo", "ch-01", [
        {"i": 2, "type": "oral", "audio": base64.b64encode(raw).decode(), "mime": "audio/webm;codecs=opus"}])
    data = json.loads((server.ROOT / path).read_text())
    name = data["answers"][0]["audio"]
    assert name == path.split("/")[-1].replace(".json", "-p2.webm")
    assert (server.ROOT / path).parent.joinpath(name).read_bytes() == raw
    assert "mime" not in data["answers"][0], "the mime must not stay in the json"


@with_test_topic
def test_rejects_missing_slug():
    expect_rejection(lambda: server.save_attempt("../outside", "ch-01", []))


@with_test_topic
def test_rejects_escaping_exam():
    expect_rejection(lambda: server.save_attempt("demo", "../../outside", []))


@with_test_topic
def test_rejects_missing_exam():
    expect_rejection(lambda: server.save_attempt("demo", "does-not-exist", []))


if __name__ == "__main__":
    test_writes_attempt()
    test_saves_oral_audio()
    test_rejects_missing_slug()
    test_rejects_escaping_exam()
    test_rejects_missing_exam()
    print("ok")
