"""Per-scene illustration loader + image manifest tests for Black Spire.

Runs headless (dummy video driver).  Verifies the node-6 illustration contract:

  * every scene references an image slot in the manifest
  * every slot resolves to an on-disk PNG of the fixed illustration size
  * no dangling (orphan) manifest entries
  * the per-scene loader (keyed by scene id) returns a valid surface for every
    scene, caches it, and reports the same filename the manifest assigns
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import unittest

import pygame

from black_spire import art, story


def setUpModule():
    pygame.init()


def tearDownModule():
    pygame.quit()


class ManifestTests(unittest.TestCase):
    def test_manifest_exists_and_loads(self):
        self.assertTrue(os.path.exists(art.MANIFEST_PATH))
        manifest = art.load_manifest()
        self.assertIsInstance(manifest, dict)
        self.assertEqual(len(manifest), len(story.SCENES))

    def test_validate_image_manifest_is_clean(self):
        self.assertEqual(art.validate_image_manifest(story.SCENES), [])

    def test_every_scene_references_an_image_slot(self):
        manifest = art.load_manifest()
        missing = sorted(set(story.SCENES) - set(manifest))
        self.assertEqual(missing, [], "scenes missing a manifest slot: %s" % missing)

    def test_no_orphan_manifest_entries(self):
        manifest = art.load_manifest()
        orphan = sorted(set(manifest) - set(story.SCENES))
        self.assertEqual(orphan, [], "orphan manifest entries: %s" % orphan)

    def test_every_slot_resolves_to_a_real_png(self):
        manifest = art.load_manifest()
        for sid, filename in manifest.items():
            path = art.image_path(filename)
            self.assertTrue(filename.endswith(".png"), "%s -> %r" % (sid, filename))
            self.assertTrue(os.path.exists(path), "%s -> %s" % (sid, path))


class LoaderTests(unittest.TestCase):
    def test_loader_keyed_by_scene_id_returns_every_scene(self):
        ill = art.Illustrations()
        for sid in story.SCENES:
            surf = ill.get_scene(sid)
            self.assertEqual(surf.get_size(), art.ILLUSTRATION_SIZE, sid)

    def test_filename_for_matches_manifest(self):
        ill = art.Illustrations()
        for sid, filename in art.load_manifest().items():
            self.assertEqual(ill.filename_for(sid), filename, sid)

    def test_loader_caches_surfaces(self):
        ill = art.Illustrations()
        first = ill.get_scene(story.START_SCENE)
        second = ill.get_scene(story.START_SCENE)
        self.assertIs(first, second)

    def test_missing_scene_id_raises(self):
        ill = art.Illustrations()
        with self.assertRaises(KeyError):
            ill.get_scene("no_such_scene")


if __name__ == "__main__":
    unittest.main()
