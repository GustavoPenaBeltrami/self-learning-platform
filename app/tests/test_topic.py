#!/usr/bin/env python3
import base64, json, os, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import store

PNG = b"\x89PNG\r\n\x1a\nfake"


def with_temp_topics(f):
    def wrapped():
        tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
        real = store.ROOT, store.TOPICS
        store.ROOT, store.TOPICS = tmp, tmp / "topics"
        (store.TOPICS / "demo" / "notes").mkdir(parents=True)
        (store.TOPICS / "demo" / "topic.json").write_text(json.dumps({"title": "Demo", "order": 2, "goals": ["g"]}))
        try:
            f()
        finally:
            store.ROOT, store.TOPICS = real
            shutil.rmtree(tmp)
    return wrapped


def notes():
    return sorted(p.name for p in (store.TOPICS / "demo" / "notes").glob("*.md"))


def save(html, **extra):
    return store.save_topic("demo", {"html": html, "stamp": store.read_topic("demo")["stamp"], **extra})


def raises(kind, f):
    try:
        f()
    except kind:
        return True
    return False


@with_temp_topics
def test_split_rename_and_keep_meta():
    r = save("<h1>One</h1><p>a</p><h1>Two</h1><p>b</p>", title="New", subtitle="s")
    assert r["ok"] and notes() == ["01-one.md", "02-two.md"] == r["sections"], r
    save("<h1>Uno</h1><p>a</p>")
    assert notes() == ["01-uno.md"], "renamed and removed sections are deleted"
    saved = json.loads((store.TOPICS / "demo" / "topic.json").read_text())
    assert saved == {"title": "New", "subtitle": "s", "order": 2, "goals": ["g"]}, saved
    assert "<h1>Uno</h1>" in store.read_topic("demo")["html"]


@with_temp_topics
def test_html_absent_keeps_notes():
    save("<h1>One</h1><p>a</p>")
    r = store.save_topic("demo", {"title": "Only meta"})
    assert notes() == ["01-one.md"] and r["sections"] == ["01-one.md"]
    assert store.read_topic("demo")["title"] == "Only meta"
    assert raises(ValueError, lambda: store.save_topic("demo", {"html": 3, "stamp": store.read_topic("demo")["stamp"]}))


@with_temp_topics
def test_stale_stamp_conflicts():
    old = store.read_topic("demo")["stamp"]
    (store.TOPICS / "demo" / "notes" / "05-agent.md").write_text("# Agent\n\nwritten by an agent\n")
    try:
        store.save_topic("demo", {"html": "<h1>One</h1>", "stamp": old})
    except store.Conflict as e:
        assert e.extra["stamp"] == store.read_topic("demo")["stamp"] != old
    else:
        raise AssertionError("a stale stamp must conflict")
    assert raises(store.Conflict, lambda: store.save_topic("demo", {"html": "<h1>One</h1>"})), "html needs a stamp"
    assert notes() == ["05-agent.md"], "a conflict must not touch notes"
    new = save("<h1>One</h1>")["stamp"]
    assert new == store.read_topic("demo")["stamp"]


@with_temp_topics
def test_images_extract_dedupe_and_gc():
    data = "data:image/png;base64," + base64.b64encode(PNG).decode()
    save(f'<h1>A</h1><p><img src="{data}"></p><p><img src="{data}"></p>')
    img = store.TOPICS / "demo" / "notes" / "img"
    files = list(img.iterdir())
    assert len(files) == 1 and files[0].read_bytes() == PNG, files
    md = (store.TOPICS / "demo" / "notes" / "01-a.md").read_text()
    assert f'src="img/{files[0].name}"' in md and "base64" not in md, md
    assert f'src="/topics/demo/notes/img/{files[0].name}"' in store.read_topic("demo")["html"]
    uploaded = store.save_image("demo", "image/webp", b"RIFFxxxxWEBP")["src"].split("/")[-1]
    (img / "mine.png").write_bytes(PNG)
    old = 0
    for f in (files[0], img / uploaded):
        os.utime(f, (old, old))
    save("<h1>A</h1><p>no images</p>")
    assert sorted(p.name for p in img.iterdir()) == ["mine.png"], "gc drops old unreferenced hashed files only"
    fresh = store.save_image("demo", "image/png", PNG)["src"].split("/")[-1]
    save("<h1>A</h1><p>still none</p>")
    assert (img / fresh).exists(), "a just-uploaded image survives a stale autosave"
    assert raises(ValueError, lambda: store.save_image("demo", "image/svg+xml", b"<svg/>"))
    assert raises(ValueError, lambda: save('<h1>A</h1><img src="data:image/png;base64,@@@">'))


@with_temp_topics
def test_links_validation():
    ok = [{"title": "MDN", "url": "https://developer.mozilla.org"}, {"title": "Book", "path": "~/b.pdf"}]
    store.save_topic("demo", {"links": ok})
    assert store.read_topic("demo")["links"] == ok
    for bad in ("x", [{"title": "x", "url": "javascript:alert(1)"}], [{"url": "https://x"}],
                [{"title": "x"}], [{"title": "x", "url": "https://x", "path": "/y"}]):
        assert raises(ValueError, lambda: store.save_topic("demo", {"links": bad})), bad


@with_temp_topics
def test_traversal_and_symlink():
    for slug in ("..", "../demo", "a/b", "", ".hidden", "demo/../demo"):
        assert raises(store.NotFound, lambda: store.read_topic(slug)), slug
    ext = pathlib.Path(tempfile.mkdtemp()).resolve()
    try:
        (ext / "notes").mkdir()
        (ext / "notes" / "01-a.md").write_text("# A\n")
        os.symlink(ext, store.TOPICS / "linked")
        assert "linked" in [t["slug"] for t in store.topics()]
        assert "<h1>A</h1>" in store.read_topic("linked")["html"], "a symlinked topic opens"
    finally:
        shutil.rmtree(ext)


@with_temp_topics
def test_bad_topic_json_and_ordering():
    for slug, content in (("broken", "{nope"), ("list", "[1]"), ("strorder", '{"title": "Zed", "order": "1"}'),
                          ("badorder", '{"title": "Bad", "order": "x"}'), ("alpha", '{"title": "Alpha", "order": 2}')):
        (store.TOPICS / slug).mkdir()
        (store.TOPICS / slug / "topic.json").write_text(content)
    (store.TOPICS / "broken" / "exams" / "e").mkdir(parents=True)
    (store.TOPICS / "broken" / "exams" / "e" / "exam.json").write_text("{bad")
    assert [t["slug"] for t in store.topics()] == ["strorder", "alpha", "demo", "badorder", "broken", "list"]
    exams = {t["slug"]: t["exams"] for t in store.exam_index()["topics"]}
    assert exams["broken"] == [{"path": "topics/broken/exams/e/exam.json", "title": "e"}]


@with_temp_topics
def test_resources_and_sources():
    r = store.save_resource("demo", "My notes (v2).pdf", b"%PDF")
    assert r == {"ok": True, "name": "My notes (v2).pdf", "url": "/topics/demo/resources/My%20notes%20%28v2%29.pdf"}, r
    assert raises(store.Conflict, lambda: store.save_resource("demo", "My notes (v2).pdf", b"x"))
    for bad in ("../x.pdf", "a/b.pdf", ".env.txt", "noext", "", "x.pdf\n"):
        assert raises(ValueError, lambda: store.save_resource("demo", bad, b"x")), bad
    assert [x["name"] for x in store.resources(store.TOPICS / "demo")] == ["My notes (v2).pdf"]
    book = store.ROOT / "book.pdf"
    book.write_bytes(b"%PDF-1")
    store.save_topic("demo", {"links": [{"title": "web", "url": "https://x.org"}, {"title": "b", "path": str(book)},
                                        {"title": "gone", "path": "~/no/such/file.pdf"}]})
    assert store.source_file("demo", "1") == (book, "application/pdf")
    for i in ("0", "2", "9", "x", "-1", ""):
        assert raises(store.NotFound, lambda: store.source_file("demo", i)), i


@with_temp_topics
def test_sections_sort_numerically():
    d = store.TOPICS / "demo" / "notes"
    for name in ("100-z.md", "11-y.md", "02-x.md"):
        (d / name).write_text("# " + name + "\n")
    assert [f.name for f in store.sections(store.TOPICS / "demo")] == ["02-x.md", "11-y.md", "100-z.md"]


if __name__ == "__main__":
    test_split_rename_and_keep_meta()
    test_html_absent_keeps_notes()
    test_stale_stamp_conflicts()
    test_images_extract_dedupe_and_gc()
    test_links_validation()
    test_traversal_and_symlink()
    test_bad_topic_json_and_ordering()
    test_resources_and_sources()
    test_sections_sort_numerically()
    print("ok")
