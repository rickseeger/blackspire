"""Automated smoke test for the Black Spire slice.

Runs headless (dummy video + audio drivers).  Verifies:

  * the story graph has no dead ends (every choice resolves to a valid scene)
  * walking every choice dynamically lands on a valid next scene
  * there is a continuation path AND a death path
  * the death scene triggers the single death bell exactly once
  * scene text + illustration both render (right text, left picture)
  * the farmer is defined in the character sheet, and the farm illustration
    contains the sheet's tunic color (picture matches the written description)
  * every sound asset (ambient + action + bell) loads with non-zero length
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest

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


class GraphTests(unittest.TestCase):
    def test_graph_is_valid(self):
        self.assertEqual(story.validate_graph(), [], "story graph has dead ends")

    def test_start_scene_exists(self):
        self.assertIn(story.START_SCENE, story.SCENES)

    def test_continuation_path(self):
        engine = story.StoryEngine()
        for idx in (0, 0, 0, 1):   # farm -> errand -> return -> road -> castle_gate
            engine.choose(idx)
        self.assertEqual(engine.current, "castle_gate")

    def test_death_path(self):
        engine = story.StoryEngine()
        for idx in (0, 0, 0, 0):   # farm -> errand -> return -> road -> death
            engine.choose(idx)
        self.assertEqual(engine.current, story.DEATH_SCENE)

    def test_walk_every_choice_resolves(self):
        for sid, scene in story.SCENES.items():
            for i, choice in enumerate(scene.choices):
                engine = story.StoryEngine(start=sid)
                result = engine.choose(i)
                self.assertIn(result, story.SCENES,
                              "%s choice %d (%r) -> %r" % (sid, i, choice.label, result))


class CharacterSheetTests(unittest.TestCase):
    def test_farmer_defined(self):
        self.assertIn("farmer", CHARACTERS)
        entry = CHARACTERS["farmer"]
        self.assertTrue(entry["description"].strip())
        self.assertIn("tunic", entry["description"])
        self.assertIn("tunic", entry["palette"])

    def test_farm_illustration_matches_sheet(self):
        # The written description says "patched brown tunic"; assert the farm
        # picture actually contains that exact tunic color.
        tunic = CHARACTERS["farmer"]["palette"]["tunic"]
        surf = pygame.image.load(art.image_path("farm"))
        self.assertEqual(surf.get_size(), art.ILLUSTRATION_SIZE)
        self.assertTrue(self._contains(surf, tunic, tolerance=4),
                        "farm illustration lacks the tunic color %s" % (tunic,))

    @staticmethod
    def _contains(surf, color, tolerance=4):
        w, h = surf.get_size()
        for x in range(0, w, 4):
            for y in range(0, h, 4):
                px = surf.get_at((x, y))
                if all(abs(px[i] - color[i]) <= tolerance for i in range(3)):
                    return True
        return False


class AssetTests(unittest.TestCase):
    def test_all_illustrations_load(self):
        for sid, scene in story.SCENES.items():
            surf = pygame.image.load(art.image_path(scene.image))
            self.assertEqual(surf.get_size(), art.ILLUSTRATION_SIZE, sid)

    def test_all_sounds_load_and_have_length(self):
        am = audio.AudioManager()
        names = [n for n in list(audio.AMBIENTS.values()) + list(audio.ACTIONS.values()) if n]
        for name in names:
            snd = pygame.mixer.Sound(am._path(name))
            self.assertGreater(snd.get_length(), 0.0, name)

    def test_ambient_beds_and_bell_exist(self):
        self.assertIn("farm", audio.AMBIENTS)
        self.assertIn("road", audio.AMBIENTS)
        self.assertIn("bell", audio.ACTIONS)  # the single death bell


class RenderTests(unittest.TestCase):
    def test_scene_text_renders_with_illustration(self):
        game = Game()
        for sid in story.SCENES:
            game.story.current = sid
            game._enter_scene(sid)
            info = game.render()
            self.assertEqual(info["illustration"], art.ILLUSTRATION_SIZE, sid)
            self.assertGreater(info["title"][0], 0, sid)
            if sid == "farm":
                self.assertGreater(info["choices"], 0)

    def test_death_triggers_bell_once(self):
        game = Game()
        for idx in (0, 0, 0, 0):   # farm -> errand -> return -> road -> death
            game.navigate(idx)
        self.assertEqual(game.story.current, story.DEATH_SCENE)
        self.assertEqual(game.audio.bell_count, 1)
        game.navigate(0)           # "Try again" -> back to the farm
        self.assertEqual(game.story.current, "farm")

    def test_choice_triggers_action_sound(self):
        game = Game()
        game.navigate(0)           # farm -> errand (no action sound)
        game.navigate(0)           # errand -> return (action sound "run")
        self.assertEqual(game.audio.last_action, "run")


if __name__ == "__main__":
    unittest.main()
