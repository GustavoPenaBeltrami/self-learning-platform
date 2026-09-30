#!/usr/bin/env python3
import json, pathlib, shutil, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "server"))
import store


def test_schedule():
    at = "2026-09-26T10:00"
    cases = [
        ([], None, (0, True, None)),
        (["again"], "2026-09-26T09:00", (0, True, "2026-09-26T09:00")),
        (["good"], "2026-09-26T09:00", (1, False, "2026-09-27T09:00")),
        (["good"], "2026-09-25T10:00", (1, True, "2026-09-26T10:00")),
        (["good", "good"], "2026-09-24T10:00", (2, False, "2026-09-27T10:00")),
        (["good", "good"], "2026-09-23T10:00", (2, True, "2026-09-26T10:00")),
        (["good"] * 3, "2026-09-22T10:00", (3, False, "2026-09-27T10:00")),
        (["good"] * 6, "2026-09-01T10:00", (6, False, "2026-10-11T10:00")),
        (["good"] * 7, "2026-09-01T10:00", (7, False, None)),
        (["good"] * 9, "2026-01-01T10:00", (7, False, None)),
        (["good", "good", "again", "good"], "2026-09-25T10:00", (1, True, "2026-09-26T10:00")),
        (["good"] * 7 + ["again"], "2026-09-26T09:59", (0, True, "2026-09-26T09:59")),
    ]
    for recalls, last, want in cases:
        assert store.schedule(recalls, last, at) == want, (recalls, last, want)
    assert store.schedule(["good", "good"], "2026-09-22T10:00", at, [3, 4]) == (2, True, "2026-09-26T10:00")
    assert store.schedule(["good"] * 3, "2026-09-22T10:00", at, [3, 4]) == (3, False, None)


def test_card_config():
    tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
    real = store.ROOT
    store.ROOT = tmp
    try:
        assert store.read_card_config() == {"intervals": store.INTERVALS, "default": store.INTERVALS}
        assert store.save_card_config({"intervals": [3, 4]}) == {"intervals": [3, 4], "default": store.INTERVALS}
        assert json.loads((tmp / "settings.json").read_text())["cards"] == {"intervals": [3, 4]}
        for bad in ([], [0], [1.5], [True], ["3"], [3651], list(range(1, 22)), None):
            expect_rejection(lambda: store.save_card_config({"intervals": bad}))
        (tmp / "settings.json").write_text('{"global": {}, "cards": {"intervals": [0]}}')
        assert store.read_card_config() == {"intervals": store.INTERVALS, "default": store.INTERVALS}, "hand-broken file reads as defaults"
    finally:
        store.ROOT = real
        shutil.rmtree(tmp)


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
        assert [c["front"] for c in idx["demo"]["sets"][0]["index"]] == ["fa", "fb"] and idx["empty"]["sets"] == [], idx

        assert store.save_reviews("demo", [{"id": "a", "recall": "good"}]) == {"ok": True, "due": 1}
        lines = (c / "reviews.jsonl").read_text().splitlines()
        assert lines[1] == "broken" and json.loads(lines[2])["id"] == "a", "appends on a new line"
        deck = store.read_deck("demo")
        assert [x["id"] for x in deck["cards"]] == ["b", "a"], "due first"
        a = deck["cards"][1]
        assert (a["box"], a["due"], a["learned"], a["front"], a["note"]) == (1, False, False, "fa", "A › B") and a["last"] and a["next"]
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
        assert deck["cards"][0]["note"] == "A", "a card belongs to its H1 only"
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


def test_card_sets():
    tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
    real = store.TOPICS
    store.TOPICS = tmp
    try:
        (tmp / "demo" / "notes").mkdir(parents=True)
        (tmp / "demo" / "notes" / "01-a.md").write_text("# A\n\n## B\n")
        (tmp / "demo" / "notes" / "02-empty.md").write_text("# Empty\n")
        store.upsert_card("demo", {"front": "from note", "back": "b", "note": "A › B"})
        store.upsert_card("demo", {"front": "custom", "back": "b", "set": " Verbs "})
        store.upsert_card("demo", {"front": "loose", "back": "b"})
        deck = store.upsert_card("demo", {"front": "picked", "back": "b", "set": "A"})
        assert {c["front"]: c["set"] for c in deck["cards"]} == {"from note": "A", "custom": "Verbs", "loose": "unsorted", "picked": "A"}
        assert [(x["name"], x["file"], x["cards"]) for x in deck["sets"]] == [("A", "01-a.md", 2), ("Verbs", None, 1), ("unsorted", None, 1)]
        assert deck["notes"] == ["A", "Empty"], "notes without cards have no set"
        saved = {c["front"]: c for c in json.loads((tmp / "demo" / "cards" / "cards.json").read_text())}
        assert saved["picked"]["note"] == "A" and "set" not in saved["picked"], "a note set is stored as the note"
        assert saved["custom"]["set"] == "Verbs"
        deck = store.upsert_card("demo", {"id": saved["custom"]["id"], "front": "custom", "back": "b", "set": ""})
        assert "set" not in json.loads((tmp / "demo" / "cards" / "cards.json").read_text())[1], "clearing the set drops it"
        expect_rejection(lambda: store.upsert_card("demo", {"front": "f", "back": "b", "set": 1}))
    finally:
        store.TOPICS = real
        shutil.rmtree(tmp)


def test_set_rename_and_bulk_delete():
    tmp = pathlib.Path(tempfile.mkdtemp()).resolve()
    real = store.TOPICS
    store.TOPICS = tmp
    try:
        (tmp / "demo" / "notes").mkdir(parents=True)
        (tmp / "demo" / "notes" / "01-a.md").write_text("# A\n")
        (tmp / "demo" / "notes" / "02-b.md").write_text("# B\n")
        for front in ("one", "two"):
            store.upsert_card("demo", {"front": front, "back": "x", "note": "A"})
        store.upsert_card("demo", {"front": "three", "back": "x", "set": "Verbs"})
        deck = store.save_set("demo", {"from": "A", "name": "Nouns", "note": "A", "cards": [
            {"id": "one", "front": "one!", "back": "x"}, {"front": "new", "back": "y"}, {"front": " ", "back": ""}]})
        got = {c["front"]: (c["set"], c["note"]) for c in deck["cards"]}
        assert got == {"one!": ("Nouns", "A"), "new": ("Nouns", "A"), "three": ("Verbs", "")}, "two dropped from the form is deleted"
        deck = store.save_set("demo", {"from": "Verbs", "name": "", "note": "B", "cards": [{"id": "three", "front": "three", "back": "x"}]})
        assert next(c for c in deck["cards"] if c["front"] == "three")["set"] == "B", "a set named after its note is that note's set"
        deck = store.save_set("demo", {"name": "Fresh", "note": None, "cards": [{"front": "q", "back": ""}]})
        assert next(c for c in deck["cards"] if c["front"] == "q")["set"] == "Fresh"
        expect_rejection(lambda: store.save_set("demo", {"name": "Fresh", "cards": []}))
        expect_rejection(lambda: store.save_set("demo", {"name": "", "note": "", "cards": []}))
        expect_rejection(lambda: store.save_set("demo", {"name": "unsorted", "cards": []}))
        deck = store.save_set("demo", {"from": "Nouns", "name": "Nouns", "note": None, "cards": [
            {"id": "one", "front": "one", "back": "x"}, {"id": "new", "front": "new", "back": "y"}, {"id": "two", "front": "two", "back": "x"}]})
        assert {c["front"] for c in deck["cards"] if c["set"] == "Nouns"} == {"one", "new", "two"}
        deck = store.delete_card("demo", ["one"])
        assert {c["front"] for c in deck["cards"]} == {"new", "two", "three", "q"}
        expect_rejection(lambda: store.delete_card("demo", ["two", "ghost"]))
        expect_rejection(lambda: store.delete_sets("demo", ["Nouns", "ghost"]))
        assert store.delete_sets("demo", ["Nouns", "B", "Fresh"])["cards"] == []
    finally:
        store.TOPICS = real
        shutil.rmtree(tmp)


if __name__ == "__main__":
    test_manual_cards()
    test_card_sets()
    test_schedule()
    test_card_config()
    test_deck()
    test_set_rename_and_bulk_delete()
    print("ok")
