"""Node-8 character-sheet + illustration consistency tests.

Runs headless (dummy video driver).  Verifies the node-8 completion contract at
the code level only -- no image-perception tool is used:

  * every scene shows its final illustration (manifest wired, real AI art on
    disk, not a flat placeholder)
  * every recurring character is rendered from their fixed written description
    in every scene they appear in (verbatim injection, no drift, no orphan cast)

Subjective art quality is the human playtester's call, not this node's.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest

import pygame

from black_spire import art, consistency, story


def setUpModule():
    pygame.init()


def tearDownModule():
    pygame.quit()


class CharacterConsistencyTests(unittest.TestCase):
    def test_character_consistency_is_clean(self):
        self.assertEqual(
            consistency.validate_character_consistency(story.SCENES), [])

    def test_combined_consistency_is_clean(self):
        self.assertEqual(consistency.validate_consistency(story.SCENES), [])

    def test_sheet_has_all_recurring_characters(self):
        sheet = consistency.load_character_sheet()
        self.assertEqual(set(sheet), set(consistency.CHARACTER_HEADINGS))
        for key, desc in sheet.items():
            self.assertTrue(desc.strip(), key)
            self.assertTrue(desc.strip().endswith("."), key)

    def test_every_scene_lists_known_characters(self):
        scene_chars = consistency.load_scene_characters()
        self.assertEqual(set(scene_chars), set(story.SCENES))
        for sid, chars in scene_chars.items():
            self.assertTrue(chars, "%s has an empty cast" % sid)
            self.assertEqual(len(set(chars)), len(chars), "%s duplicate cast" % sid)
            for key in chars:
                self.assertIn(key, consistency.CHARACTER_HEADINGS,
                              "%s -> %r" % (sid, key))

    def test_every_scene_prompt_injects_the_fixed_descriptions_verbatim(self):
        sheet = consistency.load_character_sheet()
        scene_chars = consistency.load_scene_characters()
        prompts = consistency.load_image_prompts()
        for sid, chars in scene_chars.items():
            block = consistency.characters_block(prompts[sid]["prompt"])
            self.assertIsNotNone(block, "%s has no Characters block" % sid)
            expected = " ".join(sheet[key] for key in chars)
            self.assertEqual(block, expected, sid)


class IllustrationWiringTests(unittest.TestCase):
    def test_every_scene_resolves_to_a_real_illustration(self):
        # Each scene's manifest slot must point at real AI art, not a flat
        # placeholder: require substantial color diversity across the whole set.
        manifest = art.load_manifest()
        for sid in story.SCENES:
            filename = manifest[sid]
            surf = pygame.image.load(art.image_path(filename))
            self.assertEqual(surf.get_size(), art.ILLUSTRATION_SIZE, sid)
            self.assertGreater(
                self._unique_colors(surf), 300,
                "%s -> %s looks like a flat placeholder" % (sid, filename))

    @staticmethod
    def _unique_colors(surf, step=3):
        w, h = surf.get_size()
        colors = set()
        for x in range(0, w, step):
            for y in range(0, h, step):
                colors.add(tuple(surf.get_at((x, y))))
        return len(colors)


if __name__ == "__main__":
    unittest.main()
