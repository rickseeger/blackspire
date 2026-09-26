"""Automated smoke test for the complete Black Spire story (68 scenes).

Runs headless (dummy video + audio drivers).  Verifies:

  * the story graph is valid (no dangling choices, start scene present)
  * scale: >= 60 scenes, many death endings, several good endings
  * choice breadth: 2-4 choices on every non-terminal scene, exactly one
    restart choice on every terminal scene
  * every choice resolves to a valid next scene id
  * every scene AND every death/good ending is reachable from the start
  * the three required distinct good endings are present (punish the king,
    prevent it from happening again, escape together)
  * walking a death path tolls the single death bell exactly once
  * walking a good-ending path never tolls the bell
  * a choice-triggered action sound fires
  * every scene's text + illustration render headless
  * the farmer is defined in the character sheet and the farm illustration is
    real AI art (high color diversity, not a flat placeholder)
  * every sound asset loads with non-zero length
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest
from collections import deque

import pygame

from black_spire import art, audio, story
from black_spire.app import Game
from black_spire.characters import CHARACTERS


def setUpModule():
    pygame.init()
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(22050, -16, 1, 512)
    pygame.mixer.set_num_channels(16)
    pygame.mixer.set_reserved(1)


def tearDownModule():
    pygame.quit()


def _forward_edges():
    """Forward graph; terminal (death/good) scenes are sinks."""
    edges = {}
    for sid, sc in story.SCENES.items():
        if sc.kind in ("death", "good"):
            edges[sid] = []
        else:
            edges[sid] = [c.target for c in sc.choices]
    return edges


def _path_to(target):
    """BFS a list of scene ids from START_SCENE to ``target``."""
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
    """Drive ``game`` along ``path`` by picking each scene's matching choice."""
    for nxt in path[1:]:
        idx = next(i for i, c in enumerate(game.story.choices()) if c.target == nxt)
        game.navigate(idx)


class GraphTests(unittest.TestCase):
    def test_graph_is_valid(self):
        self.assertEqual(story.validate_graph(), [], "story graph has problems")

    def test_start_scene_exists(self):
        self.assertIn(story.START_SCENE, story.SCENES)

    def test_scale(self):
        self.assertGreaterEqual(len(story.SCENES), 60)
        self.assertGreaterEqual(len(story.DEATH_SCENES), 12)
        self.assertGreaterEqual(len(story.GOOD_ENDINGS), 3)

    def test_choice_breadth(self):
        for sid, sc in story.SCENES.items():
            if sc.kind in ("death", "good"):
                self.assertEqual(len(sc.choices), 1, sid)
                self.assertEqual(sc.choices[0].target, story.START_SCENE, sid)
            else:
                self.assertGreaterEqual(len(sc.choices), 2, sid)
                self.assertLessEqual(len(sc.choices), 4, sid)

    def test_every_choice_resolves(self):
        for sid, sc in story.SCENES.items():
            for i, ch in enumerate(sc.choices):
                self.assertIn(ch.target, story.SCENES, "%s choice %d" % (sid, i))

    def test_all_scenes_reachable(self):
        edges = _forward_edges()
        seen = {story.START_SCENE}
        q = deque([story.START_SCENE])
        while q:
            cur = q.popleft()
            for nxt in edges[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        self.assertEqual(len(seen), len(story.SCENES),
                         "unreachable scenes: %s"
                         % sorted(set(story.SCENES) - seen))

    def test_all_endings_reachable(self):
        for sid in sorted(story.DEATH_SCENES | story.GOOD_ENDINGS):
            self.assertIsNotNone(_path_to(sid), "%s unreachable" % sid)

    def test_required_good_endings_present(self):
        required = {"good_punish", "good_break_spell", "good_escape"}
        self.assertTrue(required.issubset(story.GOOD_ENDINGS),
                        "missing required endings: %s"
                        % sorted(required - story.GOOD_ENDINGS))


class CharacterSheetTests(unittest.TestCase):
    def test_farmer_defined(self):
        self.assertIn("farmer", CHARACTERS)
        entry = CHARACTERS["farmer"]
        self.assertTrue(entry["description"].strip())
        self.assertIn("tunic", entry["description"])
        self.assertIn("tunic", entry["palette"])

    def test_cast_is_complete(self):
        for key in ("farmer", "wife", "king", "wizard", "dragon", "herald",
                    "neighbor", "captain", "servant", "queen_ghost"):
            self.assertIn(key, CHARACTERS)
            self.assertTrue(CHARACTERS[key]["description"].strip(), key)

    def test_farm_illustration_is_real_art_not_placeholder(self):
        # The placeholder drawings were flat vector art with a handful of
        # solid colors (< 30 unique).  A genuine cinematic AI painting has
        # thousands, so require substantial color diversity to prove the
        # node-3 art set has not regressed to a programmatic drawing.
        surf = pygame.image.load(art.image_path("farm.png"))
        self.assertEqual(surf.get_size(), art.ILLUSTRATION_SIZE)
        self.assertGreater(self._unique_colors(surf), 1000,
                           "farm illustration looks flat (placeholder?)")

    @staticmethod
    def _unique_colors(surf, step=2):
        w, h = surf.get_size()
        colors = set()
        for x in range(0, w, step):
            for y in range(0, h, step):
                colors.add(tuple(surf.get_at((x, y))))
        return len(colors)


class AssetTests(unittest.TestCase):
    def test_all_illustrations_load(self):
        ill = art.Illustrations()
        for sid, sc in story.SCENES.items():
            surf = ill.get_scene(sid)
            self.assertEqual(surf.get_size(), art.ILLUSTRATION_SIZE, sid)

    def test_all_sounds_load_and_have_length(self):
        am = audio.AudioManager()
        names = [n for n in list(audio.AMBIENTS.values()) + list(audio.ACTIONS.values()) if n]
        for name in names:
            snd = pygame.mixer.Sound(am._path(name))
            self.assertGreater(snd.get_length(), 0.0, name)

    def test_ambient_beds_and_bell_exist(self):
        for amb in ("farm", "village", "road", "mountain", "wood", "castle", "spire"):
            self.assertIn(amb, audio.AMBIENTS)
        self.assertIn("bell", audio.ACTIONS)  # the single death bell


class RenderTests(unittest.TestCase):
    def test_scene_text_renders_with_illustration(self):
        game = Game()
        try:
            for sid, sc in story.SCENES.items():
                game.story.current = sid
                game._enter_scene(sid)
                info = game.render()
                self.assertEqual(info["illustration"], art.ILLUSTRATION_SIZE, sid)
                self.assertGreater(info["title"][0], 0, sid)
                if sc.kind == "scene":
                    self.assertGreaterEqual(info["choices"], 2, sid)
        finally:
            pygame.quit()

    def test_death_triggers_bell_once(self):
        game = Game()
        try:
            path = _path_to(sorted(story.DEATH_SCENES)[0])
            _navigate(game, path)
            self.assertIn(game.story.current, story.DEATH_SCENES)
            self.assertEqual(game.audio.bell_count, 1)
            game.navigate(0)  # "Try again" -> back to the start
            self.assertEqual(game.story.current, story.START_SCENE)
        finally:
            pygame.quit()

    def test_good_ending_never_tolls_bell(self):
        game = Game()
        try:
            _navigate(game, _path_to("good_punish"))
            self.assertEqual(game.story.current, "good_punish")
            self.assertEqual(game.audio.bell_count, 0)
        finally:
            pygame.quit()

    def test_choice_triggers_action_sound(self):
        game = Game()
        try:
            game.navigate(0)  # farm -> errand (soft steps)
            self.assertEqual(game.story.current, "errand")
            self.assertEqual(game.audio.last_action, "steps")
            game.navigate(0)  # errand -> return (running)
            self.assertEqual(game.story.current, "return")
            self.assertEqual(game.audio.last_action, "run")
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
