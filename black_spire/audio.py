"""Layered audio for Black Spire.

Model: one always-on ambient bed per scene (looped on a reserved channel),
one-shot action sounds layered on top when a choice plays out, and a single
large death-bell toll on the death scene.  All assets are procedurally
generated (see tools/generate_assets.py), so there are no licensing concerns
and the files stay small.
"""

import os

import pygame

from .story import DEATH_BELL


ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")

# ambient bed -> wav filename ("none" means silence)
AMBIENTS = {
    "farm": "farm_ambient.wav",
    "road": "road_ambient.wav",
    "none": None,
}

# one-shot action / effect sound id -> wav filename
ACTIONS = {
    "run": "action_run.wav",
    "gallop": "action_gallop.wav",
    "scream": "action_scream.wav",
    "bell": "death_bell.wav",
}


class AudioManager:
    def __init__(self, asset_dir=ASSET_DIR, enabled=True):
        self.asset_dir = asset_dir
        self.enabled = enabled
        self.current_ambient = None
        self.bell_count = 0
        self.last_action = None
        self._loaded = {}

    def _path(self, filename):
        return os.path.join(self.asset_dir, filename)

    def load(self, sound_id):
        if sound_id in self._loaded:
            return self._loaded[sound_id]
        filename = ACTIONS.get(sound_id) or AMBIENTS.get(sound_id)
        if not filename:
            raise KeyError("unknown sound id %r" % sound_id)
        path = self._path(filename)
        if not os.path.exists(path):
            raise FileNotFoundError("missing sound asset %s" % path)
        snd = pygame.mixer.Sound(path)
        self._loaded[sound_id] = snd
        return snd

    # -- ambient bed ---------------------------------------------------
    def play_ambient(self, ambient_id):
        if not self.enabled:
            self.current_ambient = ambient_id
            return
        if ambient_id == self.current_ambient:
            return
        self.stop_ambient()
        self.current_ambient = ambient_id
        filename = AMBIENTS.get(ambient_id)
        if not filename:
            return  # "none" => silence
        snd = self.load(ambient_id)
        pygame.mixer.Channel(0).play(snd, loops=-1)
        pygame.mixer.Channel(0).set_volume(0.55)

    def stop_ambient(self):
        if self.enabled:
            pygame.mixer.Channel(0).stop()
        self.current_ambient = None

    # -- one-shot action sounds ---------------------------------------
    def play_action(self, sound_id, volume=0.9):
        self.last_action = sound_id
        if not self.enabled:
            return
        snd = self.load(sound_id)
        ch = snd.play()
        if ch is not None:
            ch.set_volume(volume)

    # -- death bell ----------------------------------------------------
    def play_bell(self, volume=1.0):
        self.bell_count += 1
        self.play_action(DEATH_BELL, volume=volume)
