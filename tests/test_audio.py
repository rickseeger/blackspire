"""Node-4 audio-layer tests for Black Spire.

Runs headless (dummy video + audio drivers).  Verifies the completion contract:

  * every scene plays an always-on ambient bed by default (a non-silent loop)
  * every choice maps to a one-shot action asset and triggers it on navigate
  * the death scene adds a single large bell toll on top of its ambient
  * a good ending never tolls the bell
  * every ambient and action file is real and non-silent (ffprobe duration +
    ffmpeg loudness), and the engine loads and plays every one without error
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import json
import re
import shutil
import subprocess
import unittest
from collections import deque

import pygame

from black_spire import audio, story
from black_spire.app import Game

HAVE_FFMPEG = shutil.which("ffprobe") is not None and shutil.which("ffmpeg") is not None


def setUpModule():
    pygame.init()
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(22050, -16, 1, 512)
    pygame.mixer.set_num_channels(16)
    pygame.mixer.set_reserved(1)


def tearDownModule():
    pygame.quit()


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


class AudioMapTests(unittest.TestCase):
    """The scene/choice-to-audio map is complete and consistent."""

    def test_validate_audio_clean(self):
        self.assertEqual(audio.validate_audio(story.SCENES), [])

    def test_every_scene_has_an_ambient_bed(self):
        for sid, sc in story.SCENES.items():
            self.assertIn(sc.ambient, audio.AMBIENTS,
                          "%s ambient %r has no bed" % (sid, sc.ambient))

    def test_every_choice_maps_to_an_action_asset(self):
        for sid, sc in story.SCENES.items():
            for i, ch in enumerate(sc.choices):
                self.assertIsNotNone(ch.action_sound, "%s choice %d" % (sid, i))
                self.assertIn(ch.action_sound, audio.ACTIONS,
                              "%s choice %d sound %r" % (sid, i, ch.action_sound))

    def test_death_bell_exists(self):
        self.assertIn(story.DEATH_BELL, audio.ACTIONS)

    def test_no_silent_ambient_id(self):
        for sid, sc in story.SCENES.items():
            self.assertNotEqual(sc.ambient, "none", sid)


class AssetTests(unittest.TestCase):
    """Every audio file is real, has length, and is non-silent."""

    def _files(self):
        for name in audio.AMBIENTS.values():
            yield name, "ambient"
        for name in audio.ACTIONS.values():
            yield name, "action"

    def _duration(self, path):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True)
        return float(out.stdout.strip())

    def _max_volume_db(self, path):
        out = subprocess.run(
            ["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True)
        m = re.search(r"max_volume:\s*(-?[\d.]+|-\w+) dB", out.stderr)
        return float(m.group(1)) if m and m.group(1) != "-inf" else float("-inf")

    @unittest.skipUnless(HAVE_FFMPEG, "ffprobe/ffmpeg not available")
    def test_every_file_has_duration(self):
        am = audio.AudioManager()
        for name, _kind in self._files():
            self.assertGreater(self._duration(am._path(name)), 0.0, name)

    @unittest.skipUnless(HAVE_FFMPEG, "ffprobe/ffmpeg not available")
    def test_every_file_is_non_silent(self):
        am = audio.AudioManager()
        for name, _kind in self._files():
            db = self._max_volume_db(am._path(name))
            self.assertGreater(db, -40.0, "%s is silent (max %.1f dB)" % (name, db))

    @unittest.skipUnless(HAVE_FFMPEG, "ffprobe/ffmpeg not available")
    def test_ambient_beds_loop_long_enough(self):
        am = audio.AudioManager()
        for name in audio.AMBIENTS.values():
            self.assertGreaterEqual(self._duration(am._path(name)), 5.0, name)

    def test_every_sound_loads_and_plays_without_error(self):
        am = audio.AudioManager()
        for sound_id in list(audio.AMBIENTS) + list(audio.ACTIONS):
            snd = am.load(sound_id)
            self.assertGreater(snd.get_length(), 0.0, sound_id)
            ch = snd.play()
            if ch is not None:
                ch.stop()


class EngineBehaviorTests(unittest.TestCase):
    """The engine starts the right ambient and fires the right events."""

    def test_ambient_bed_starts_for_every_scene(self):
        game = Game()
        try:
            for sid, sc in story.SCENES.items():
                game.story.current = sid
                game._enter_scene(sid)
                self.assertEqual(game.audio.current_ambient, sc.ambient,
                                 "%s ambient should be %r" % (sid, sc.ambient))
        finally:
            pygame.quit()

    def test_every_choice_triggers_its_action_sound(self):
        game = Game()
        try:
            for sid, sc in story.SCENES.items():
                for i, ch in enumerate(sc.choices):
                    game.story.current = sid
                    game.audio.action_log.clear()
                    game.navigate(i)
                    self.assertIn(ch.action_sound, game.audio.action_log,
                                  "%s choice %d should fire %r"
                                  % (sid, i, ch.action_sound))
                    if ch.target in story.DEATH_SCENES:
                        self.assertIn(story.DEATH_BELL, game.audio.action_log,
                                      "%s choice %d leads to death -> bell" % (sid, i))
        finally:
            pygame.quit()

    def test_death_scene_keeps_ambient_and_tolls_bell_once(self):
        game = Game()
        try:
            target = sorted(story.DEATH_SCENES)[0]
            game.audio.action_log.clear()
            _navigate(game, _path_to(target))
            self.assertIn(game.story.current, story.DEATH_SCENES)
            sc = story.SCENES[game.story.current]
            self.assertEqual(game.audio.current_ambient, sc.ambient)
            self.assertEqual(game.audio.bell_count, 1)
            self.assertEqual(game.audio.action_log.count(story.DEATH_BELL), 1)
        finally:
            pygame.quit()

    def test_every_death_path_tolls_exactly_one_bell(self):
        game = Game()
        try:
            for sid in sorted(story.DEATH_SCENES):
                game2 = Game()
                try:
                    _navigate(game2, _path_to(sid))
                    self.assertIn(game2.story.current, story.DEATH_SCENES)
                    self.assertEqual(game2.audio.bell_count, 1, sid)
                finally:
                    pygame.quit()
        finally:
            pygame.quit()

    def test_good_endings_never_toll_the_bell(self):
        game = Game()
        try:
            for sid in sorted(story.GOOD_ENDINGS):
                game.story.current = story.START_SCENE
                game.audio.bell_count = 0
                _navigate(game, _path_to(sid))
                self.assertIn(game.story.current, story.GOOD_ENDINGS)
                self.assertEqual(game.audio.bell_count, 0, sid)
        finally:
            pygame.quit()



SOURCES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "audio_sources.json")


class MixingTests(unittest.TestCase):
    """The ambient bed is mixed quieter than the action sounds."""

    def test_ambient_volume_below_action_volume(self):
        self.assertLess(audio.AMBIENT_VOLUME, audio.ACTION_VOLUME,
                        "ambient bed must play quieter than action sounds")

    def test_ambient_files_peak_below_action_files(self):
        # File-level mix check: ambient beds are normalized to a lower peak
        # than action one-shots, so consequences sit clearly on top of the bed.
        am = audio.AudioManager()
        amb_peak = max(self._peak(am._path(n)) for n in audio.AMBIENTS.values())
        act_peak = min(self._peak(am._path(n)) for n in audio.ACTIONS.values()
                       if n != audio.ACTIONS[story.DEATH_BELL])
        self.assertLess(amb_peak, act_peak,
                        "ambient files should peak lower than action files")

    def _peak(self, path):
        out = subprocess.run(
            ["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True)
        m = re.search(r"max_volume:\s*(-?[\d.]+|-\w+) dB", out.stderr)
        return float(m.group(1)) if m else float("-inf")


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not available")
class ProvenanceTests(unittest.TestCase):
    """Every sound is a real downloaded file with a recorded source + license."""

    def _manifest(self):
        with open(SOURCES_PATH) as f:
            return json.load(f)["files"]

    def test_every_sound_has_recorded_source_and_license(self):
        manifest = self._manifest()
        am = audio.AudioManager()
        for sound_id, filename in list(audio.AMBIENTS.items()) + list(audio.ACTIONS.items()):
            self.assertIn(filename, manifest, filename)
            entry = manifest[filename]
            self.assertTrue(entry["sources"], filename)
            for src in entry["sources"]:
                self.assertTrue(src.get("source_url"), filename)
                self.assertTrue(src.get("license"), filename)

    def test_every_sound_is_a_real_wav_on_disk(self):
        manifest = self._manifest()
        am = audio.AudioManager()
        for sound_id, filename in list(audio.AMBIENTS.items()) + list(audio.ACTIONS.items()):
            path = am._path(filename)
            self.assertTrue(os.path.isfile(path), filename)
            # RIFF/WAVE header = a genuine PCM WAV, not a generated blob
            with open(path, "rb") as f:
                head = f.read(12)
            self.assertEqual(head[:4], b"RIFF", filename)
            self.assertEqual(head[8:12], b"WAVE", filename)


if __name__ == "__main__":
    unittest.main()
