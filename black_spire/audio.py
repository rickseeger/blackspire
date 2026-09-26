"""Layered audio for Black Spire.

Model: one always-on ambient bed per scene (looped on a reserved channel),
one-shot action sounds layered on top when a choice plays out, and a single
large death-bell toll on the death scene.

The scene -> ambient bed and choice -> action-sound relationships live in
``story.py`` (the ``Scene.ambient`` and ``Choice.action_sound`` fields); this
module maps those ids to on-disk wav files under ``assets/audio/``.  Every
asset is a real recording downloaded from Wikimedia Commons (a CC0 /
public-domain / CC-BY archive) -- nothing is synthesized.  Source URLs and
licenses for every file are recorded in ``docs/audio_sources.json`` (+ .md).
"""

import os

import pygame

from .story import DEATH_BELL


ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")

# ambient bed id -> wav filename (looped on channel 0)
AMBIENTS = {
    "farm": "farm_ambient.wav",        # chickens + sheep + morning wind
    "village": "village_ambient.wav",  # market murmur + distant bell + rooster
    "road": "road_ambient.wav",        # open-road wind + distant hooves
    "mountain": "mountain_ambient.wav",# high wind + skittering stones
    "wood": "wood_ambient.wav",        # leaves + crickets + owl + wolf
    "castle": "castle_ambient.wav",    # torch crackle + court murmur + stone
    "spire": "spire_ambient.wav",      # magical hum + fire roar + high wind
}

# one-shot action / effect sound id -> wav filename
ACTIONS = {
    "steps": "action_steps.wav",       # soft walking footsteps
    "run": "action_run.wav",           # running footsteps
    "gallop": "action_gallop.wav",     # a horse galloping
    "scream": "action_scream.wav",     # a scream on a fall
    "door": "action_door.wav",         # a door creaking open
    "fire": "action_fire.wav",         # flame whoosh / crackle
    "sword": "action_sword.wav",       # a sword clash
    "splash": "action_splash.wav",     # water splashing
    "wolf": "action_wolf.wav",         # a wolf howl
    "roar": "action_roar.wav",         # a dragon roar
    "stone": "action_stone.wav",       # rocks clattering
    "magic": "action_magic.wav",       # a magical shimmer
    "whisper": "action_whisper.wav",   # a ghostly whisper
    "creak": "action_creak.wav",       # a stair / floorboard creak
    "gasp": "action_gasp.wav",         # a sharp breath
    "chains": "action_chains.wav",     # iron chains clanking
    "bell": "death_bell.wav",          # the single death bell
}


# Mix levels: the always-on ambient bed is mixed quieter than the one-shot
# action sounds, so consequences are clearly audible on top of the bed.
AMBIENT_VOLUME = 0.55
ACTION_VOLUME = 0.9


def validate_audio(scenes):
    """Return a list of problems linking ``scenes`` to this module's ids.

    An empty list means every scene's ambient bed and every choice's action
    sound resolves to a known asset id.
    """
    problems = []
    for sid, scene in scenes.items():
        if scene.ambient not in AMBIENTS:
            problems.append("%s ambient %r unknown" % (sid, scene.ambient))
        for i, choice in enumerate(scene.choices):
            if choice.action_sound not in ACTIONS:
                problems.append("%s choice %d action_sound %r unknown"
                                % (sid, i, choice.action_sound))
    return problems


class AudioManager:
    def __init__(self, asset_dir=ASSET_DIR, enabled=True):
        self.asset_dir = asset_dir
        self.enabled = enabled
        self.current_ambient = None
        self.bell_count = 0
        self.last_action = None
        self.action_log = []      # every action/bell event, in order
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
            raise KeyError("unknown ambient id %r" % ambient_id)
        snd = self.load(ambient_id)
        pygame.mixer.Channel(0).play(snd, loops=-1)
        pygame.mixer.Channel(0).set_volume(AMBIENT_VOLUME)

    def stop_ambient(self):
        if self.enabled:
            pygame.mixer.Channel(0).stop()
        self.current_ambient = None

    # -- one-shot action sounds ---------------------------------------
    def play_action(self, sound_id, volume=ACTION_VOLUME):
        self.last_action = sound_id
        self.action_log.append(sound_id)
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
