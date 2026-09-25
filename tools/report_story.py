"""Scene/choice/ending report for Black Spire (engine-parseable, walkable).

Walks the story graph from the start scene and reports:

  * counts: scenes, choices, death endings, good endings
  * edge integrity: every choice resolves to a valid scene id (no dangling)
  * reachability: every scene, death ending and good ending is reachable from
    the start scene via forward edges (terminal scenes are treated as sinks)
  * a concrete walk path to each death and good ending

Run from the repo root:

    .venv/bin/python tools/report_story.py            # print to stdout
    .venv/bin/python tools/report_story.py --write    # also write docs/story_report.txt
"""

import argparse
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from black_spire import story  # noqa: E402


def forward_edges():
    """Edges of the forward graph: terminal (death/good) scenes are sinks."""
    edges = {}
    for sid, scene in story.SCENES.items():
        if scene.kind in ("death", "good"):
            edges[sid] = []
        else:
            edges[sid] = [c.target for c in scene.choices]
    return edges


def reachable_from_start(edges):
    """BFS from the start scene; returns the set of visited ids."""
    seen = {story.START_SCENE}
    q = deque([story.START_SCENE])
    while q:
        cur = q.popleft()
        for nxt in edges.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen


def path_to(edges, target):
    """Return a list of scene ids from START_SCENE to ``target`` (BFS)."""
    prev = {story.START_SCENE: None}
    q = deque([story.START_SCENE])
    while q:
        cur = q.popleft()
        if cur == target:
            out = []
            while cur is not None:
                out.append(cur)
                cur = prev[cur]
            return list(reversed(out))
        for nxt in edges.get(cur, []):
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    return None


def build_report():
    lines = []
    add = lines.append

    total = len(story.SCENES)
    deaths = sorted(story.DEATH_SCENES)
    goods = sorted(story.GOOD_ENDINGS)
    nonterminal = [s for s in story.SCENES.values() if s.kind == "scene"]
    n_choices = sum(len(s.choices) for s in story.SCENES.values())

    add("=" * 70)
    add("BLACK SPIRE - SCENE / CHOICE / ENDING REPORT")
    add("=" * 70)
    add("")
    add("Scene count      : %d" % total)
    add("Choice count     : %d" % n_choices)
    add("Death endings    : %d" % len(deaths))
    add("Good endings     : %d" % len(goods))
    add("Average choices  : %.2f per scene" % (n_choices / total))
    add("")

    # --- edge integrity (no dangling) ---
    add("-" * 70)
    add("EDGE INTEGRITY")
    add("-" * 70)
    problems = story.validate_graph()
    add("validate_graph() problems: %d" % len(problems))
    for p in problems:
        add("  ! %s" % p)
    add("Every choice resolves to a valid scene id: %s"
        % ("YES" if not problems else "NO"))
    add("")

    # --- choice-count histogram ---
    add("-" * 70)
    add("CHOICE-COUNT DISTRIBUTION (non-terminal scenes)")
    add("-" * 70)
    hist = {}
    for s in nonterminal:
        hist[len(s.choices)] = hist.get(len(s.choices), 0) + 1
    for k in sorted(hist):
        add("  %d choice(s): %d scenes" % (k, hist[k]))
    add("")

    # --- reachability ---
    edges = forward_edges()
    seen = reachable_from_start(edges)
    add("-" * 70)
    add("REACHABILITY (forward walk from '%s')" % story.START_SCENE)
    add("-" * 70)
    unreachable = [sid for sid in story.SCENES if sid not in seen]
    add("Scenes reachable: %d / %d" % (len(seen), total))
    if unreachable:
        for sid in sorted(unreachable):
            add("  ! UNREACHABLE scene: %s" % sid)
    else:
        add("All %d scenes reachable from start: YES" % total)
    add("")

    # --- endings ---
    add("-" * 70)
    add("DEATH ENDINGS (%d)" % len(deaths))
    add("-" * 70)
    for sid in deaths:
        p = path_to(edges, sid)
        add("  [%-16s] %-22s  path(%d): %s"
            % (sid, story.SCENES[sid].title, len(p), " -> ".join(p)))
    add("")
    add("-" * 70)
    add("GOOD ENDINGS (%d)" % len(goods))
    add("-" * 70)
    for sid in goods:
        p = path_to(edges, sid)
        add("  [%-16s] %-22s  path(%d): %s"
            % (sid, story.SCENES[sid].title, len(p), " -> ".join(p)))
    add("")

    # --- per-character spot check ---
    add("-" * 70)
    add("CAST (from characters.py)")
    add("-" * 70)
    try:
        from black_spire.characters import CHARACTERS
        for key, c in CHARACTERS.items():
            add("  %-10s %-24s %s" % (key, c["name"], c["description"]))
    except Exception as exc:  # pragma: no cover
        add("  (could not load characters.py: %s)" % exc)
    add("")
    add("=" * 70)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Black Spire story report")
    ap.add_argument("--write", action="store_true",
                    help="also write docs/story_report.txt")
    args = ap.parse_args(argv)

    text = build_report()
    print(text)

    if args.write:
        outdir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "docs")
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, "story_report.txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("\n[wrote %s]" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
