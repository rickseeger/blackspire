"""Node-7 exhaustive path-walk tests for the integrated Black Spire game.

Runs headless (dummy video + audio drivers).  Verifies the completion contract:

  * every reachable path is walked through every choice (edge-covering traversal
    of the real engine)
  * every scene renders without error and its ambient/action audio loads and
    plays without error
  * every choice reaches a valid next scene id (no dangling references)
  * every declared ending (all death endings AND all good endings) is reachable
  * a coverage report is emitted showing every scene visited and every ending
    reached, and it fails on any dangling choice / audio / image reference

Only code-level and pixel-sampling assertions are used; no image-perception
tool.  Story/audio/art data is never modified.
"""

import json
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from black_spire import art, audio, coverage, story

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")


def setUpModule():
    pygame.init()
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(22050, -16, 1, 512)
    pygame.mixer.set_num_channels(16)
    pygame.mixer.set_reserved(1)


def tearDownModule():
    pygame.quit()


class ReferenceIntegrityTests(unittest.TestCase):
    """Fail on any dangling choice, audio, or image reference."""

    def test_story_graph_has_no_dangling_choices(self):
        self.assertEqual(story.validate_graph(), [])

    def test_audio_map_has_no_dangling_references(self):
        self.assertEqual(audio.validate_audio(story.SCENES), [])

    def test_image_manifest_has_no_dangling_references(self):
        self.assertEqual(art.validate_image_manifest(story.SCENES), [])

    def test_combined_reference_integrity_clean(self):
        self.assertEqual(coverage.reference_integrity(), [])


class ExhaustiveWalkTests(unittest.TestCase):
    """One exhaustive edge-covering walk of the integrated engine."""

    @classmethod
    def setUpClass(cls):
        cls.result = coverage.walk(verify_render=True)
        cls.txt_path, cls.json_path = coverage.write_reports(cls.result, DOCS_DIR)

    def test_walk_records_no_problems(self):
        self.assertEqual(
            self.result.problems, [],
            "walk found %d problem(s):\n%s"
            % (len(self.result.problems), "\n".join("  - " + p for p in self.result.problems)))

    def test_every_scene_visited(self):
        missing = sorted(set(story.SCENES) - set(self.result.scenes_visited))
        self.assertEqual(missing, [], "scenes never visited: %s" % missing)

    def test_every_death_ending_reached(self):
        missing = sorted(story.DEATH_SCENES - set(self.result.deaths_reached))
        self.assertEqual(missing, [], "death endings never reached: %s" % missing)

    def test_every_good_ending_reached(self):
        missing = sorted(story.GOOD_ENDINGS - set(self.result.goods_reached))
        self.assertEqual(missing, [], "good endings never reached: %s" % missing)

    def test_every_choice_traversed(self):
        all_edges = {"%s[%d]" % (sid, i)
                     for sid, sc in story.SCENES.items()
                     for i in range(len(sc.choices))}
        missing = sorted(all_edges - set(self.result.edges_traversed))
        self.assertEqual(missing, [], "choices never traversed: %s" % missing)

    def test_coverage_report_emitted(self):
        self.assertTrue(os.path.exists(self.txt_path), "missing %s" % self.txt_path)
        self.assertTrue(os.path.exists(self.json_path), "missing %s" % self.json_path)
        with open(self.txt_path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("RESULT: PASS", text)
        self.assertIn("SCENE COVERAGE", text)
        self.assertIn("ENDING COVERAGE", text)
        self.assertIn("EDGE COVERAGE", text)
        with open(self.json_path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["scenes_visited"]), len(story.SCENES))
        self.assertEqual(len(data["deaths_reached"]), len(story.DEATH_SCENES))
        self.assertEqual(len(data["goods_reached"]), len(story.GOOD_ENDINGS))
        self.assertEqual(len(data["edges_traversed"]), len(
            [c for s in story.SCENES.values() for c in s.choices]))


class RenderCoverageTests(unittest.TestCase):
    """Independently render every scene headless and sample the framebuffer."""

    def test_every_scene_renders_a_non_blank_frame(self):
        from black_spire.app import Game
        game = Game()
        try:
            for sid in story.SCENES:
                game.story.current = sid
                game._enter_scene(sid)
                game.render()
                # pixel-sample the drawn surface: it must not be a single flat color
                surface = game.screen
                w, h = surface.get_size()
                samples = {
                    surface.get_at((x, y))[:3]
                    for x in (0, w // 2, w - 1)
                    for y in (0, h // 2, h - 1)
                }
                self.assertGreater(len(samples), 1,
                                   "%s rendered a blank/flat frame" % sid)
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
