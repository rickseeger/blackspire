"""Exhaustive walk + coverage report for Black Spire (node 7).

Drives the real ``black_spire.app.Game`` headless and walks every choice edge
of the story graph from the root, verifying at each step that:

  * the scene renders without error (illustration present, title + choices drawn)
  * the scene's ambient bed is playing (matches ``Scene.ambient``)
  * each choice fires its mapped action sound
  * each choice lands on a valid next scene id (no dangling reference)
  * each death scene tolls the bell exactly once; a good ending never tolls it
  * every scene is visited and every death/good ending is reached

The walk is an *edge-covering* traversal: it visits every scene and traverses
every choice exactly once.  That is the meaningful reading of "walk every
reachable path" for this graph -- it contains cycles (e.g. gate <-> guards),
so exhaustive simple-path enumeration is unbounded work (~12M simple paths),
while edge + node + ending coverage captures exactly what the contract asks for
("every scene visited and every ending reached", "fails on any dangling choice,
audio, or image reference").

It returns a :class:`CoverageResult` that can be rendered to a text + JSON
coverage report (see :func:`write_reports`).
"""

import json
import os
from collections import deque
from dataclasses import asdict, dataclass, field

import pygame

from . import art, audio, story
from .app import Game


def forward_edges(scenes):
    """Forward graph; terminal (death/good) scenes are sinks."""
    edges = {}
    for sid, sc in scenes.items():
        edges[sid] = [] if sc.kind in ("death", "good") else [c.target for c in sc.choices]
    return edges


def path_to(edges, target):
    """BFS a scene-id path from START_SCENE to ``target``, or None if unreachable."""
    start = story.START_SCENE
    prev = {start: None}
    q = deque([start])
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


@dataclass
class CoverageResult:
    scenes_total: int = 0
    choices_total: int = 0
    deaths_total: int = 0
    goods_total: int = 0
    scenes_visited: list = field(default_factory=list)       # sorted scene ids
    deaths_reached: list = field(default_factory=list)       # sorted death ids
    goods_reached: list = field(default_factory=list)        # sorted good ids
    edges_traversed: list = field(default_factory=list)      # "sid[i] -> target"
    ending_paths: dict = field(default_factory=dict)         # ending id -> "a -> b -> c"
    problems: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.problems and self._coverage_complete()

    def _coverage_complete(self):
        return (
            len(self.scenes_visited) == self.scenes_total
            and len(self.deaths_reached) == self.deaths_total
            and len(self.goods_reached) == self.goods_total
            and len(self.edges_traversed) == self.choices_total
        )

    def to_dict(self):
        return asdict(self)


def _check_scene(game, sid, problems, verify_render):
    """Assert the engine is on ``sid`` and it renders + plays the right ambient."""
    scene = story.SCENES[sid]
    if game.story.current != sid:
        problems.append("expected current scene %r, got %r" % (sid, game.story.current))
        return
    if game.audio.current_ambient != scene.ambient:
        problems.append("%r ambient: got %r want %r"
                        % (sid, game.audio.current_ambient, scene.ambient))
    surf = game.illustrations.get_scene(sid)  # loads via the image manifest
    if surf.get_size() != art.ILLUSTRATION_SIZE:
        problems.append("%r illustration size %r (want %r)"
                        % (sid, surf.get_size(), art.ILLUSTRATION_SIZE))
    if verify_render:
        info = game.render()
        if info.get("illustration") != art.ILLUSTRATION_SIZE:
            problems.append("%r rendered illustration %r"
                            % (sid, info.get("illustration")))
        if info.get("title", (0, 0))[0] <= 0:
            problems.append("%r rendered an empty title" % sid)
        expected = 1 if scene.kind in ("death", "good") else len(scene.choices)
        if info.get("choices") != expected:
            problems.append("%r rendered %d choices, want %d"
                            % (sid, info.get("choices"), expected))


def _check_bell(game, sid, expected, problems):
    if game.audio.bell_count != expected:
        problems.append("%r bell_count=%d (want %d)" % (sid, game.audio.bell_count, expected))


def walk(verify_render=True):
    """Run the exhaustive edge-covering walk against the real engine."""
    scenes = story.SCENES
    edges = forward_edges(scenes)
    paths = {sid: path_to(edges, sid) for sid in scenes}

    result = CoverageResult(
        scenes_total=len(scenes),
        choices_total=sum(len(s.choices) for s in scenes.values()),
        deaths_total=len(story.DEATH_SCENES),
        goods_total=len(story.GOOD_ENDINGS),
    )
    problems = result.problems
    visited = set()
    deaths_reached = set()
    goods_reached = set()
    edges_traversed = set()
    ending_paths = {}

    game = Game()
    try:
        for sid in sorted(scenes):
            scene = scenes[sid]
            path = paths[sid]
            if path is None:
                problems.append("scene %r unreachable from start" % sid)
                continue
            for idx, choice in enumerate(scene.choices):
                label = "%s[%d]" % (sid, idx)
                try:
                    # reset to start and drive along a real path to ``sid``
                    game.story.current = story.START_SCENE
                    game.audio.bell_count = 0
                    game.audio.action_log.clear()
                    game._enter_scene(story.START_SCENE)
                    for nxt in path[1:]:
                        j = next(i for i, c in enumerate(game.story.choices())
                                 if c.target == nxt)
                        game.navigate(j)

                    if game.story.current != sid:
                        problems.append("drive to %r landed on %r"
                                        % (sid, game.story.current))
                        continue

                    visited.add(sid)
                    _check_scene(game, sid, problems, verify_render)
                    if scene.kind == "death":
                        deaths_reached.add(sid)
                        ending_paths.setdefault(sid, " -> ".join(path))
                        _check_bell(game, sid, 1, problems)
                    elif scene.kind == "good":
                        goods_reached.add(sid)
                        ending_paths.setdefault(sid, " -> ".join(path))
                        _check_bell(game, sid, 0, problems)

                    # traverse the outgoing edge and verify the landing
                    target = choice.target
                    if target not in scenes:
                        problems.append("dangling choice: %s (%r) -> %r"
                                        % (label, choice.label, target))
                        continue
                    game.audio.action_log.clear()
                    game.navigate(idx)
                    edges_traversed.add(label)
                    if game.story.current != target:
                        problems.append("%s (%r) landed on %r, want %r"
                                        % (label, choice.label, game.story.current, target))
                        continue

                    visited.add(target)
                    _check_scene(game, target, problems, verify_render)
                    if choice.action_sound and choice.action_sound not in game.audio.action_log:
                        problems.append("%s (%r) did not fire action sound %r"
                                        % (label, choice.label, choice.action_sound))
                    if target in story.DEATH_SCENES:
                        deaths_reached.add(target)
                        ending_paths.setdefault(target, " -> ".join(path + [target]))
                        _check_bell(game, target, 1, problems)
                    elif target in story.GOOD_ENDINGS:
                        goods_reached.add(target)
                        ending_paths.setdefault(target, " -> ".join(path + [target]))
                        _check_bell(game, target, 0, problems)
                except Exception as exc:  # noqa: BLE001 - a missing asset/ref surfaces here
                    problems.append("%s (%r -> %r) raised %s: %s"
                                    % (label, choice.label, choice.target,
                                       type(exc).__name__, exc))
    finally:
        pygame.quit()

    result.scenes_visited = sorted(visited)
    result.deaths_reached = sorted(deaths_reached)
    result.goods_reached = sorted(goods_reached)
    result.edges_traversed = sorted(edges_traversed)
    result.ending_paths = ending_paths
    return result


def reference_integrity():
    """Return the combined dangling-reference problems (choice / audio / image)."""
    return (
        story.validate_graph()
        + audio.validate_audio(story.SCENES)
        + art.validate_image_manifest(story.SCENES)
    )


def render_text(result):
    lines = []
    add = lines.append

    def missing(have, want):
        return sorted(set(want) - set(have))

    missing_scenes = missing(result.scenes_visited, story.SCENES)
    missing_deaths = missing(result.deaths_reached, story.DEATH_SCENES)
    missing_goods = missing(result.goods_reached, story.GOOD_ENDINGS)

    # every (sid, idx) pair is an edge; compare against the actual choice set
    all_edges = {"%s[%d]" % (sid, i)
                 for sid, sc in story.SCENES.items()
                 for i in range(len(sc.choices))}
    missing_edges = sorted(all_edges - set(result.edges_traversed))

    add("=" * 72)
    add("BLACK SPIRE - EXHAUSTIVE WALK COVERAGE REPORT (node 7)")
    add("=" * 72)
    add("scenes total  : %d" % result.scenes_total)
    add("choices total : %d" % result.choices_total)
    add("death endings : %d" % result.deaths_total)
    add("good endings  : %d" % result.goods_total)
    add("")

    add("-" * 72)
    add("SCENE COVERAGE")
    add("-" * 72)
    add("scenes visited : %d / %d" % (len(result.scenes_visited), result.scenes_total))
    add("missing scenes : %s" % (", ".join(missing_scenes) if missing_scenes else "(none)"))
    add("")

    add("-" * 72)
    add("ENDING COVERAGE")
    add("-" * 72)
    add("death endings reached : %d / %d" % (len(result.deaths_reached), result.deaths_total))
    for sid in result.deaths_reached:
        add("  [death] %-16s %s" % (sid, result.ending_paths.get(sid, "")))
    if missing_deaths:
        add("  MISSING deaths: %s" % ", ".join(missing_deaths))
    add("good endings reached  : %d / %d" % (len(result.goods_reached), result.goods_total))
    for sid in result.goods_reached:
        add("  [good ] %-16s %s" % (sid, result.ending_paths.get(sid, "")))
    if missing_goods:
        add("  MISSING goods: %s" % ", ".join(missing_goods))
    add("")

    add("-" * 72)
    add("EDGE COVERAGE (every choice traversed)")
    add("-" * 72)
    add("choices traversed : %d / %d" % (len(result.edges_traversed), result.choices_total))
    if missing_edges:
        add("  MISSING edges: %s" % ", ".join(missing_edges))
    else:
        add("  every choice traversed exactly once: YES")
    add("")

    add("-" * 72)
    add("PROBLEMS (%d)" % len(result.problems))
    add("-" * 72)
    if result.problems:
        for p in result.problems:
            add("  ! " + p)
    else:
        add("  (none)")
    add("")

    add("RESULT: %s" % ("PASS" if result.ok else "FAIL"))
    add("=" * 72)
    return "\n".join(lines)


def write_reports(result, docs_dir):
    """Write coverage_report.txt and coverage_report.json under ``docs_dir``."""
    os.makedirs(docs_dir, exist_ok=True)
    txt_path = os.path.join(docs_dir, "coverage_report.txt")
    json_path = os.path.join(docs_dir, "coverage_report.json")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(render_text(result) + "\n")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, sort_keys=True)
    return txt_path, json_path
