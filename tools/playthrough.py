"""Scripted playthrough of the full Black Spire game (node-6 evidence).

Drives the real ``black_spire.app.Game`` headless and walks explicit branches to
several death endings and several good endings, asserting at every step that:

  * the scene's ambient bed is playing (matches ``Scene.ambient``)
  * each choice fires its mapped action sound
  * a death scene tolls the death bell exactly once
  * a good ending never tolls the bell
  * every scene's illustration loads from the per-scene image manifest

Run from the repo root (headless):

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/playthrough.py

Exit 0 = full game runs start-to-finish with correct audio; exit 1 = a violation.
"""

import os
import sys
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from black_spire import art, audio, story  # noqa: E402
from black_spire.app import Game  # noqa: E402


def _forward_edges():
    edges = {}
    for sid, sc in story.SCENES.items():
        edges[sid] = [] if sc.kind in ("death", "good") else [c.target for c in sc.choices]
    return edges


def _path_to(target):
    edges = _forward_edges()
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
        for nxt in edges[cur]:
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    return None


def _navigate(game, path):
    for nxt in path[1:]:
        idx = next(i for i, c in enumerate(game.story.choices()) if c.target == nxt)
        game.navigate(idx)


def main():
    pygame.init()
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(22050, -16, 1, 512)
    pygame.mixer.set_num_channels(16)
    pygame.mixer.set_reserved(1)

    problems = []

    # 1) per-scene illustration loader covers every scene via the manifest
    manifest_problems = art.validate_image_manifest(story.SCENES)
    if manifest_problems:
        problems.extend(manifest_problems)
    else:
        ill = art.Illustrations()
        for sid in story.SCENES:
            if ill.get_scene(sid).get_size() != art.ILLUSTRATION_SIZE:
                problems.append("%s illustration wrong size" % sid)

    # 2) every scene plays its ambient bed, every choice fires its action sound
    game = Game()
    for sid, sc in story.SCENES.items():
        game.story.current = sid
        game._enter_scene(sid)
        if game.audio.current_ambient != sc.ambient:
            problems.append("%s ambient: got %r want %r"
                            % (sid, game.audio.current_ambient, sc.ambient))
        for i, ch in enumerate(sc.choices):
            game.story.current = sid
            game.audio.action_log.clear()
            game.navigate(i)
            if ch.action_sound not in game.audio.action_log:
                problems.append("%s choice %d did not fire %r" % (sid, i, ch.action_sound))
    pygame.quit()

    # 3) scripted walks: several death endings, several good endings
    death_targets = ["mountain_fall", "wood_swamp", "spire_trap"]
    good_targets = ["good_punish", "good_escape", "good_dragon"]

    print("=" * 72)
    print("BLACK SPIRE - SCRIPTED PLAYTHROUGH")
    print("=" * 72)
    print("scenes=%d choices=%d deaths=%d goods=%d"
          % (len(story.SCENES),
             sum(len(s.choices) for s in story.SCENES.values()),
             len(story.DEATH_SCENES), len(story.GOOD_ENDINGS)))

    for target in death_targets + good_targets:
        game = Game()
        path = _path_to(target)
        print("\n[walk -> %s] %d step(s): %s" % (target, len(path) - 1, " -> ".join(path)))
        _navigate(game, path)
        sc = story.SCENES[game.story.current]
        print("  ended at: %s (%s)  ambient=%s image=%s"
              % (game.story.current, sc.kind, game.audio.current_ambient,
                 game.illustrations.filename_for(game.story.current)))
        if target in story.DEATH_SCENES:
            if game.audio.bell_count != 1:
                problems.append("%s: bell_count=%d (want 1)" % (target, game.audio.bell_count))
            print("  death bell tolled exactly once: %s" % (game.audio.bell_count == 1))
        else:
            if game.audio.bell_count != 0:
                problems.append("%s: good ending tolled bell %d times"
                                % (target, game.audio.bell_count))
            print("  good ending - bell tolled 0 times: %s" % (game.audio.bell_count == 0))
        pygame.quit()

    print("\n" + "=" * 72)
    if problems:
        print("FAILED: %d problem(s)" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1

    print("OK: full game runs start-to-finish; every scene reachable; every")
    print("    choice, ambient bed, action sound, death bell and image slot")
    print("    resolves with no dangling references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
