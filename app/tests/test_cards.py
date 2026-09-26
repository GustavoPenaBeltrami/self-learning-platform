#!/usr/bin/env python3
import json, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import store


def test_schedule():
    at = "2026-09-26T10:00"
    cases = [
        ([], None, (0, True)),
        (["again"], "2026-09-26T09:00", (0, True)),
        (["good"], "2026-09-26T09:00", (1, False)),
        (["good"], "2026-09-25T10:00", (1, True)),
        (["good", "good"], "2026-09-24T10:00", (2, False)),
        (["good", "good"], "2026-09-23T10:00", (2, True)),
        (["good"] * 5, "2026-09-20T10:00", (3, False)),
        (["good"] * 5, "2026-09-19T10:00", (3, True)),
        (["good", "good", "again", "good"], "2026-09-25T10:00", (1, True)),
        (["good", "good", "again"], "2026-09-26T09:59", (0, True)),
    ]
    for recalls, last, want in cases:
        assert store.schedule(recalls, last, at) == want, (recalls, last, want)


def expect_rejection(f):
    try:
        f()
    except ValueError:
        return
    raise AssertionError("should have rejected")


def test_deck():
    tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
    real = store.TOPICS
    store.TOPICS = tmp
    try:
        (tmp / "empty").mkdir()
        c = tmp / "demo" / "cards"
        c.mkdir(parents=True)
        (c / "cards.json").write_text(json.dumps([
            {"id": "a", "front": "fa", "back": "ba", "note": "A › B"},
            {"id": "b", "front": "fb", "back": "bb", "note": "A"}]))
        (c / "reviews.jsonl").write_text('{"at": "2026-09-26T09:00", "id": "gone", "recall": "good"}\nbroken')
        idx = {t["slug"]: t for t in store.cards_index()["topics"]}
        assert (idx["demo"]["cards"], idx["demo"]["due"], idx["empty"]["cards"]) == (2, 2, 0), idx

        assert store.save_reviews("demo", [{"id": "a", "recall": "good"}]) == {"ok": True, "due": 1}
        lines = (c / "reviews.jsonl").read_text().splitlines()
        assert lines[1] == "broken" and json.loads(lines[2])["id"] == "a", "appends on a new line"
        deck = store.read_deck("demo")
        assert [x["id"] for x in deck["cards"]] == ["b", "a"], "due first"
        a = deck["cards"][1]
        assert (a["box"], a["due"], a["front"], a["note"]) == (1, False, "fa", "A › B") and a["last"]
        assert deck["cards"][0]["last"] is None

        expect_rejection(lambda: store.save_reviews("demo", [{"id": "gone", "recall": "good"}]))
        expect_rejection(lambda: store.save_reviews("demo", [{"id": "a", "recall": "maybe"}]))
        expect_rejection(lambda: store.save_reviews("demo", {"id": "a"}))
        expect_rejection(lambda: store.save_reviews("empty", [{"id": "a", "recall": "good"}]))
        expect_rejection(lambda: store.save_reviews("../x", []))
        assert len((c / "reviews.jsonl").read_text().splitlines()) == 3, "rejected batches write nothing"
    finally:
        store.TOPICS = real
        shutil.rmtree(tmp)


def test_manual_cards():
    tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
    real = store.TOPICS
    store.TOPICS = tmp
    try:
        (tmp / "demo").mkdir()
        deck = store.upsert_card("demo", {"front": " Why is PUT idempotent? ", "back": "It replaces.", "note": "A › B"})
        assert deck["cards"][0]["id"] == "why-is-put-idempotent" and deck["cards"][0]["front"] == "Why is PUT idempotent?"
        deck = store.upsert_card("demo", {"front": "Why is PUT idempotent?", "back": "Again."})
        assert [c["id"] for c in deck["cards"]] == ["why-is-put-idempotent", "why-is-put-idempotent-2"]
        saved = json.loads((tmp / "demo" / "cards" / "cards.json").read_text())
        assert all(c["by"] == "user" for c in saved) and saved[1]["note"] == ""

        f = tmp / "demo" / "cards" / "cards.json"
        f.write_text(json.dumps(saved + [{"id": "agent-card", "front": "q", "back": "a", "note": "A", "extra": 1}]))
        store.upsert_card("demo", {"id": "agent-card", "front": "q2", "back": "a2"})
        edited = json.loads(f.read_text())[2]
        assert edited == {"id": "agent-card", "front": "q2", "back": "a2", "note": "", "extra": 1}, "edit keeps by and other fields"
        store.upsert_card("demo", {"id": "why-is-put-idempotent", "front": "f", "back": "b"})
        assert json.loads(f.read_text())[0]["by"] == "user"
        assert store.upsert_card("demo", {"front": "¿¡!?", "back": "b"})["cards"][-1]["id"] == "card"

        for bad in ({"front": "", "back": "b"}, {"front": "f", "back": "  "}, {"front": "f", "back": 1},
                    {"front": "f", "back": "b", "note": None}, {"id": "nope", "front": "f", "back": "b"}, "x"):
            expect_rejection(lambda: store.upsert_card("demo", bad))
        expect_rejection(lambda: store.upsert_card("missing", {"front": "f", "back": "b"}))

        deck = store.flag_card("demo", {"id": "agent-card", "flagged": True})
        assert [c["flagged"] for c in deck["cards"] if c["id"] == "agent-card"] == [True]
        assert {t["slug"]: t["flagged"] for t in store.cards_index()["topics"]}["demo"] == 1
        store.upsert_card("demo", {"id": "agent-card", "front": "q3", "back": "a3"})
        assert json.loads(f.read_text())[2]["flagged"] is True, "edit keeps the flag"
        store.flag_card("demo", {"id": "agent-card", "flagged": False})
        assert json.loads(f.read_text())[2]["flagged"] is False
        for bad in ({"id": "agent-card", "flagged": "yes"}, {"id": "nope", "flagged": True}, "x"):
            expect_rejection(lambda: store.flag_card("demo", bad))

        deck = store.delete_card("demo", "agent-card")
        assert "agent-card" not in [c["id"] for c in deck["cards"]]
        expect_rejection(lambda: store.delete_card("demo", "agent-card"))
    finally:
        store.TOPICS = real
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_manual_cards()
    test_schedule()
    test_deck()
    print("ok")
