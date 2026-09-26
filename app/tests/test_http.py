#!/usr/bin/env python3
import http.client, http.server, json, pathlib, shutil, sys, tempfile, threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import server, store


def call(port, method, path, body=None, headers=None, host=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
    h = {"Host": host or f"127.0.0.1:{port}", **(headers or {})}
    if body is not None and "Content-Length" not in h:
        h["Content-Length"] = str(len(body))
    for k, v in h.items():
        c.putheader(k, v)
    c.endheaders(body)
    r = c.getresponse()
    data = r.read()
    c.close()
    return r.status, dict(r.getheaders()), data


def test_http():
    tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
    real = store.ROOT, store.TOPICS
    store.ROOT, store.TOPICS = tmp, tmp / "topics"
    d = store.TOPICS / "demo"
    (d / "notes").mkdir(parents=True)
    (d / "notes" / "01-a.md").write_text("# A\n")
    (d / "resources").mkdir()
    (d / "resources" / "page.html").write_text("<script>x</script>")
    (d / "resources" / "pic.png").write_bytes(b"png")
    (tmp / ".git").mkdir()
    (tmp / ".git" / "config").write_text("secret")
    (tmp / "app").mkdir()
    (tmp / "app" / "x.js").write_text("1")
    book = tmp / "book.txt"
    book.write_text("chapter one")
    (d / "topic.json").write_text(json.dumps({"links": [{"title": "b", "path": str(book)}]}))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        get = lambda p, **kw: call(port, "GET", p, **kw)
        post = lambda p, b, **kw: call(port, "POST", p, b, **kw)
        evil = {"Origin": "https://evil.example"}

        assert post("/api/topic/demo", b'{"title":"x"}', headers=evil)[0] == 403
        assert post("/api/topic/demo", b'{"title":"x"}', host="evil.example:8321")[0] == 403
        assert get("/api/topic/demo", host=f"evil.example:{port}")[0] == 403
        assert get("/app/x.js", host=f"evil.example:{port}")[0] == 403
        assert (d / "notes" / "01-a.md").exists()
        own = {"Origin": f"http://localhost:{port}"}
        assert get("/api/topics", headers=own, host=f"localhost:{port}")[0] == 200

        for p in ("/.git/config", "/app/../.git/config", "/settings.json", "/topics/../.git/config", "/app/"):
            assert get(p)[0] == 404, p
        assert get("/app/x.js")[0] == 200
        assert get("/settings")[1]["Location"] == "/app/views/settings.html"

        s, h, body = get("/api/nope")
        assert s == 404 and "error" in json.loads(body)
        assert post("/api/nope", b"{}")[0] == 404
        assert get("/api/topic/..%2f..")[0] == 404
        assert post("/api/settings", b"[1]")[0] == 400
        assert post("/api/settings", b"{}", headers={"Content-Length": "-1"})[0] == 400
        assert post("/api/settings", b"{}", headers={"Content-Length": str(store.BODY_LIMIT + 1)})[0] == 400
        assert get("/api/fonts.css")[1]["Content-Type"].startswith("text/css")

        s, h, body = get("/api/topic/demo")
        stamp = json.loads(body)["stamp"]
        s, h, body = post("/api/topic/demo", json.dumps({"html": "<h1>B</h1>", "stamp": "old"}).encode())
        assert s == 409 and json.loads(body)["stamp"] == stamp
        s, h, body = post("/api/topic/demo", json.dumps({"html": "<h1>B</h1>", "stamp": stamp}).encode())
        assert s == 200 and json.loads(body)["sections"] == ["01-b.md"]

        s, h, body = post("/api/topic/demo/img", b"\x89PNG", headers={"Content-Type": "image/png"})
        src = json.loads(body)["src"]
        assert s == 200 and src.startswith("/topics/demo/notes/img/") and src.endswith(".png")
        s, h, body = get(src)
        assert s == 200 and body == b"\x89PNG" and "Content-Security-Policy" not in h
        assert post("/api/topic/demo/img", b"<svg/>", headers={"Content-Type": "image/svg+xml"})[0] == 400

        s, h, body = post("/api/topic/demo/resource?name=notes.txt", b"hello")
        assert s == 200 and json.loads(body)["url"] == "/topics/demo/resources/notes.txt"
        assert post("/api/topic/demo/resource?name=notes.txt", b"again")[0] == 409
        assert (d / "resources" / "notes.txt").read_bytes() == b"hello"
        assert post("/api/topic/demo/resource?name=../x.txt", b"x")[0] == 400

        s, h, body = get("/api/source?topic=demo&i=0")
        assert s == 200 and body == b"chapter one" and h["Content-Type"].startswith("text/plain")
        assert get("/api/source?topic=demo&i=1")[0] == 404

        (d / "cards").mkdir()
        (d / "cards" / "cards.json").write_text(json.dumps([{"id": "a", "front": "f", "back": "b", "note": "A"}]))
        s, h, body = get("/api/cards")
        assert s == 200 and json.loads(body)["topics"][0]["due"] == 1
        s, h, body = get("/api/cards/demo")
        assert s == 200 and json.loads(body)["cards"][0]["id"] == "a"
        assert get("/api/cards/nope")[0] == 404
        review = json.dumps({"reviews": [{"id": "a", "recall": "good"}]}).encode()
        assert post("/api/cards/demo", review, headers=evil)[0] == 403
        s, h, body = post("/api/cards/demo", review)
        assert s == 200 and json.loads(body) == {"ok": True, "due": 0}
        assert post("/api/cards/demo", b'{"reviews":[{"id":"zz","recall":"good"}]}')[0] == 400
        s, h, body = post("/api/cards/demo", json.dumps({"upsert": {"front": "New one", "back": "b"}}).encode())
        assert s == 200 and "new-one" in [c["id"] for c in json.loads(body)["cards"]]
        assert post("/api/cards/demo", b'{"upsert":{"front":"","back":"b"}}')[0] == 400
        assert post("/api/cards/demo", b'{"delete":"new-one"}')[0] == 200
        assert post("/api/cards/demo", b'{"delete":"new-one"}')[0] == 404

        assert get("/topics/demo/resources/page.html")[1].get("Content-Security-Policy") == "sandbox"
        assert "Content-Security-Policy" not in get("/topics/demo/resources/pic.png")[1]
    finally:
        srv.shutdown()
        srv.server_close()
        store.ROOT, store.TOPICS = real
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_http()
    print("ok")
