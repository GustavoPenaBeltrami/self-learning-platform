import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANUAL = {"slp-setup", "slp-init"}


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "missing frontmatter"
    return dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line and not line.startswith(" "))


def anchor(heading):
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def prose(text):
    return re.sub(r"^ *```.*?^ *```", "", text, flags=re.S | re.M)


def anchors(path):
    text = prose(path.read_text(encoding="utf-8"))
    return {anchor(h) for h in re.findall(r"^#+ (.+)$", text, re.M)}


skills = sorted((ROOT / "agent" / "skills").glob("*/SKILL.md"))
assert skills
assert {f.parent.name for f in skills} >= {"slp-cards", "slp-quiz"}
assert not (ROOT / "agent" / "skills" / "slp-review").exists() and not (ROOT / "agent" / "skills" / "slp-level").exists()
for f in skills:
    meta = {k.strip(): v.strip() for k, v in frontmatter(f.read_text(encoding="utf-8")).items()}
    name = f.parent.name
    assert meta.get("name") == name, f
    assert 0 < len(meta.get("description", "")) <= 1024, f
    assert (meta.get("disable-model-invocation") == "true") == (name in MANUAL), f

docs = skills + [ROOT / n for n in ("AGENTS.md", "CONTEXT.md", "README.md")]
docs += sorted((ROOT / "agent").glob("reference/*.md")) + sorted((ROOT / "agent").glob("skills/*/references/*.md"))
docs += [ROOT / "agent" / "agents" / "researcher.md"]
for f in docs:
    text = prose(f.read_text(encoding="utf-8"))
    for gone in ("slp-review", "slp-level", "level-check", "topics/review"):
        assert gone not in text, f"{f.relative_to(ROOT)}: mentions {gone}"
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if re.match(r"[a-z]+:|#|/", target) or "<" in target:
            continue
        path, _, frag = target.partition("#")
        dest = (f.parent / path).resolve()
        assert dest.exists(), f"{f.relative_to(ROOT)}: broken link {target}"
        if frag and dest.suffix == ".md":
            assert frag in anchors(dest), f"{f.relative_to(ROOT)}: missing anchor {target}"
    for ref in re.findall(r"`((?:agent|app)/[^`\s<*]+)`", text):
        ref = ref.split("?")[0].split("#")[0]
        assert (ROOT / ref).exists(), f"{f.relative_to(ROOT)}: missing path {ref}"

print("ok")
