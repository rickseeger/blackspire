"""Generate Black Spire's placeholder assets (audio + images) from scratch.

Run from the repo root with a dummy display driver (it never opens a window):

    SDL_VIDEODRIVER=dummy python3 tools/generate_assets.py

Audio is a LEGACY placeholder only: the shipped ``assets/audio/*.wav`` files
are now real recordings downloaded from Wikimedia Commons (see
``docs/audio_sources.md``), not the synthesized beeps this module emits.  The
synth functions are retained for reference but are not the audio source.
Images are flat fairytale-style drawings made of pygame primitives, with the
farmer drawn from the character-sheet palette so the picture matches the
written description.
"""

import math
import os
import random
import struct
import sys
import wave

# allow running as a standalone script from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from black_spire.characters import CHARACTERS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(ROOT, "assets", "audio")
IMAGE_DIR = os.path.join(ROOT, "assets", "images")

SAMPLE_RATE = 22050
SIZE = (512, 512)
W, H = SIZE


# --------------------------------------------------------------------------
# audio synthesis (pure stdlib)
# --------------------------------------------------------------------------

def _write(path, samples):
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        buf = bytearray()
        for s in samples:
            s = max(-1.0, min(1.0, s))
            buf += struct.pack("<h", int(s * 32767))
        f.writeframes(bytes(buf))


def _noise(dur, amp, rng):
    n = int(dur * SAMPLE_RATE)
    return [amp * (rng.random() * 2.0 - 1.0) for _ in range(n)]


def _lowpass(samples, alpha=0.05):
    out = []
    prev = 0.0
    for s in samples:
        prev += alpha * (s - prev)
        out.append(prev)
    return out


def _mix_into(dst, src, offset):
    for i, s in enumerate(src):
        j = offset + i
        if 0 <= j < len(dst):
            dst[j] += s
    return dst


def _fade_edges(samples, seconds=0.5):
    k = min(int(seconds * SAMPLE_RATE), len(samples) // 2)
    for i in range(k):
        g = i / k
        samples[i] *= g
        samples[-1 - i] *= g
    return samples


def _thud(freq=95.0, dur=0.08, amp=0.8):
    n = int(dur * SAMPLE_RATE)
    out = []
    for i in range(n):
        env = math.exp(-i / (n * 0.22))
        out.append(amp * env * math.sin(2 * math.pi * freq * i / SAMPLE_RATE))
    return out


def _cluck(seed):
    rng = random.Random(seed)
    out = []
    for _ in range(rng.randint(2, 4)):
        dur = rng.uniform(0.06, 0.11)
        f = rng.uniform(700, 1300)
        n = int(dur * SAMPLE_RATE)
        for i in range(n):
            env = math.exp(-i / (n * 0.35))
            out.append(0.4 * env * math.sin(2 * math.pi * f * i / SAMPLE_RATE))
        out += [0.0] * int(rng.uniform(0.02, 0.06) * SAMPLE_RATE)
    return out


def _bleat(seed):
    rng = random.Random(seed)
    dur = rng.uniform(0.7, 1.1)
    n = int(dur * SAMPLE_RATE)
    f0 = rng.uniform(430, 520)
    f1 = rng.uniform(270, 340)
    out = []
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * t
        vib = 1.0 + 0.04 * math.sin(2 * math.pi * 6.0 * t)
        env = math.sin(math.pi * t)
        out.append(0.55 * env * math.sin(2 * math.pi * f * vib * i / SAMPLE_RATE))
    return out


def _hoofbeat(seed):
    rng = random.Random(seed)
    out = []
    for _ in range(8):
        out += _thud(80, 0.05, 0.15)
        out += [0.0] * int(rng.uniform(0.12, 0.2) * SAMPLE_RATE)
    return out


def make_farm_ambient(duration=12.0):
    n = int(duration * SAMPLE_RATE)
    rng = random.Random(1234)
    out = [0.0] * n
    wind = _lowpass(_noise(duration, 0.5, rng), alpha=0.03)
    for i in range(n):
        out[i] += 0.10 * wind[i]
    _mix_into(out, _cluck(11), int(2.0 * SAMPLE_RATE))
    _mix_into(out, _bleat(22), int(3.6 * SAMPLE_RATE))
    _mix_into(out, _cluck(33), int(5.4 * SAMPLE_RATE))
    _mix_into(out, _bleat(44), int(7.2 * SAMPLE_RATE))
    _mix_into(out, _cluck(55), int(9.0 * SAMPLE_RATE))
    _mix_into(out, _bleat(66), int(10.4 * SAMPLE_RATE))
    return _fade_edges(out, 0.5)


def make_road_ambient(duration=12.0):
    n = int(duration * SAMPLE_RATE)
    rng = random.Random(5678)
    out = [0.0] * n
    wind = _lowpass(_noise(duration, 0.6, rng), alpha=0.05)
    for i in range(n):
        out[i] += 0.14 * wind[i]
    _mix_into(out, _hoofbeat(9), int(4.0 * SAMPLE_RATE))
    return _fade_edges(out, 0.5)


def make_run():
    rng = random.Random(999)
    out = []
    for _ in range(7):
        out += _thud(110, 0.06, 0.7)
        out += [0.0] * int(rng.uniform(0.09, 0.13) * SAMPLE_RATE)
    out += _lowpass(_noise(0.5, 0.3, rng), alpha=0.1)
    return out


def make_gallop():
    out = []
    for _ in range(3):
        out += _thud(90, 0.05, 0.6)
        out += [0.0] * int(0.06 * SAMPLE_RATE)
        out += _thud(90, 0.05, 0.6)
        out += [0.0] * int(0.06 * SAMPLE_RATE)
        out += _thud(110, 0.07, 0.8)
        out += [0.0] * int(0.14 * SAMPLE_RATE)
    return out


def make_scream():
    rng = random.Random(777)
    n = int(1.4 * SAMPLE_RATE)
    out = []
    f0, f1 = 950.0, 260.0
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * t
        vib = 1.0 + 0.06 * math.sin(2 * math.pi * 11.0 * t)
        trem = 0.7 + 0.3 * math.sin(2 * math.pi * 18.0 * t)
        out.append(trem * math.sin(2 * math.pi * f * vib * i / SAMPLE_RATE))
    out += _lowpass(_noise(0.4, 0.3, rng), alpha=0.08)
    peak = max(1e-9, max(abs(x) for x in out))
    return [0.9 * x / peak for x in out]


def make_bell(freq=174.0, dur=5.5):
    n = int(dur * SAMPLE_RATE)
    rng = random.Random(123)
    out = [0.0] * n
    partials = [
        (1.0, 0.0008, 0.55),
        (2.0, 0.0011, 0.28),
        (2.42, 0.0015, 0.18),
        (3.0, 0.0020, 0.12),
        (4.1, 0.0028, 0.07),
    ]
    for mult, decay, amp in partials:
        f = freq * mult
        for i in range(n):
            out[i] += amp * math.sin(2 * math.pi * f * i / SAMPLE_RATE) * math.exp(-decay * i)
    for i in range(int(0.03 * SAMPLE_RATE)):
        out[i] += rng.uniform(-0.5, 0.5) * math.exp(-i / (0.004 * SAMPLE_RATE))
    peak = max(1e-9, max(abs(x) for x in out))
    return [0.85 * x / peak for x in out]




# --------------------------------------------------------------------------
# node-4 audio layer: additional scene ambients + one-shot action sounds
# --------------------------------------------------------------------------

def _sine(freq, dur, amp):
    n = int(dur * SAMPLE_RATE)
    return [amp * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) for i in range(n)]


def _chirp(f0, f1, dur, amp):
    n = int(dur * SAMPLE_RATE)
    out = []
    phase = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / n)
        phase += 2 * math.pi * f / SAMPLE_RATE
        out.append(amp * math.sin(phase))
    return out


def _normalize(samples, peak=0.9):
    m = max(1e-9, max(abs(x) for x in samples))
    return [peak * x / m for x in samples]


def _adsr(samples, attack, release):
    n = len(samples)
    a = min(max(1, int(attack * SAMPLE_RATE)), n)
    r = min(max(1, int(release * SAMPLE_RATE)), n)
    out = list(samples)
    for i in range(a):
        out[i] *= i / a
    for i in range(r):
        out[n - 1 - i] *= i / r
    return out


def _bandpass(samples, alpha=0.08):
    lo = _lowpass(samples, alpha=alpha)
    hi = [s - l for s, l in zip(samples, lo)]
    return _lowpass(hi, alpha=alpha)


def _pulses(dur, rate, freq, amp, jitter=0.0):
    """A train of short decaying tone pips (crickets, clatter, crackle)."""
    rng = random.Random(int(freq * 1000 + rate * 7))
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    step = max(1, int(SAMPLE_RATE / rate))
    pos = 0
    while pos < n:
        ln = int(0.02 * SAMPLE_RATE)
        for j in range(ln):
            if pos + j < n:
                env = math.exp(-j / (ln * 0.3))
                out[pos + j] += amp * env * math.sin(
                    2 * math.pi * freq * j / SAMPLE_RATE)
        pos += step + int(rng.uniform(-jitter, jitter) * SAMPLE_RATE)
    return out


def make_village_ambient(duration=12.0):
    rng = random.Random(4321)
    n = int(duration * SAMPLE_RATE)
    out = [0.0] * n
    # low crowd murmur
    murmur = _lowpass(_noise(duration, 0.8, rng), alpha=0.06)
    for i in range(n):
        out[i] += 0.16 * murmur[i]
    # distant church bell, periodic
    bell = _sine(220.0, 2.5, 0.5)
    bell = _adsr(bell, 0.01, 2.0)
    for _ in range(4):
        _mix_into(out, [0.5 * b for b in bell], int(rng.uniform(0.5, 10.0) * SAMPLE_RATE))
    # a rooster-ish two-tone call
    call = _chirp(800, 500, 0.25, 0.5) + _chirp(500, 300, 0.35, 0.4)
    _mix_into(out, call, int(2.0 * SAMPLE_RATE))
    _mix_into(out, call, int(7.0 * SAMPLE_RATE))
    # distant cart rumbles
    rumble = _lowpass(_noise(0.8, 0.9, rng), alpha=0.04)
    _mix_into(out, [0.35 * x for x in rumble], int(5.0 * SAMPLE_RATE))
    return _normalize(_fade_edges(out, 0.5), 0.55)


def make_mountain_ambient(duration=12.0):
    rng = random.Random(8765)
    n = int(duration * SAMPLE_RATE)
    out = [0.0] * n
    # high thin wind
    wind = _bandpass(_noise(duration, 0.9, rng), alpha=0.03)
    for i in range(n):
        swell = 0.5 + 0.5 * math.sin(2 * math.pi * 0.11 * i / SAMPLE_RATE)
        out[i] += 0.30 * swell * wind[i]
    # occasional skittering stones
    for pos in (2.0, 5.5, 9.0):
        clatter = _pulses(1.2, 18, 1800, 0.5, jitter=0.1)
        _mix_into(out, [0.4 * x for x in clatter], int(pos * SAMPLE_RATE))
    return _normalize(_fade_edges(out, 0.5), 0.55)


def make_wood_ambient(duration=12.0):
    rng = random.Random(2468)
    n = int(duration * SAMPLE_RATE)
    out = [0.0] * n
    # wind through leaves (lighter bandpass)
    leaves = _bandpass(_noise(duration, 0.8, rng), alpha=0.05)
    for i in range(n):
        out[i] += 0.22 * leaves[i]
    # crickets, steady high chirp
    crickets = _pulses(duration, 26, 4200, 0.20, jitter=0.05)
    for i in range(n):
        out[i] += crickets[i]
    # owl hoots
    hoot = _adsr(_sine(340, 0.5, 0.6), 0.02, 0.25) + _adsr(_sine(260, 0.6, 0.5), 0.02, 0.3)
    _mix_into(out, hoot, int(3.0 * SAMPLE_RATE))
    _mix_into(out, hoot, int(8.5 * SAMPLE_RATE))
    # a distant wolf howl once
    howl = _normalize(_adsr(_chirp(300, 560, 0.9, 0.7) + _chirp(560, 380, 0.9, 0.6), 0.1, 0.4), 0.5)
    _mix_into(out, howl, int(10.0 * SAMPLE_RATE))
    return _normalize(_fade_edges(out, 0.5), 0.5)


def make_castle_ambient(duration=12.0):
    rng = random.Random(1357)
    n = int(duration * SAMPLE_RATE)
    out = [0.0] * n
    # low stone-cold drone
    drone = _lowpass(_noise(duration, 0.7, rng), alpha=0.02)
    for i in range(n):
        out[i] += 0.18 * drone[i]
    # torch crackle (fire)
    fire = _lowpass(_noise(duration, 0.9, rng), alpha=0.12)
    crackle = _pulses(duration, 40, 300, 0.4, jitter=0.2)
    for i in range(n):
        out[i] += 0.10 * fire[i] + 0.14 * crackle[i]
    # distant court murmur
    murmur = _lowpass(_noise(duration, 0.7, rng), alpha=0.05)
    for i in range(n):
        out[i] += 0.08 * murmur[i]
    return _normalize(_fade_edges(out, 0.5), 0.5)


def make_spire_ambient(duration=12.0):
    rng = random.Random(8642)
    n = int(duration * SAMPLE_RATE)
    out = [0.0] * n
    # low magical hum with slow beating
    for i in range(n):
        t = i / SAMPLE_RATE
        hum = (0.5 * math.sin(2 * math.pi * 55 * t) +
               0.35 * math.sin(2 * math.pi * 55.6 * t) +
               0.25 * math.sin(2 * math.pi * 110 * t))
        out[i] += 0.28 * hum
    # deep fire roar
    roar = _lowpass(_noise(duration, 1.0, rng), alpha=0.02)
    for i in range(n):
        out[i] += 0.20 * roar[i]
    # high wind howl at the top
    howl = _bandpass(_noise(duration, 0.8, rng), alpha=0.03)
    for i in range(n):
        swell = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(2 * math.pi * 0.07 * i / SAMPLE_RATE))
        out[i] += 0.16 * swell * howl[i]
    return _normalize(_fade_edges(out, 0.5), 0.5)


def make_steps():
    out = []
    for k in range(4):
        out += _thud(72, 0.05, 0.5)
        out += [0.0] * int(0.22 * SAMPLE_RATE)
    return _normalize(out, 0.7)


def make_door():
    rng = random.Random(313)
    creak = _chirp(180, 90, 1.1, 0.7)
    wood = _bandpass(_noise(1.1, 0.5, rng), alpha=0.1)
    out = [c + 0.25 * w for c, w in zip(creak, wood)]
    out += _thud(60, 0.06, 0.6)  # latch clunk at the end
    return _normalize(_adsr(out, 0.01, 0.3), 0.75)


def make_fire():
    rng = random.Random(7777)
    n = int(1.4 * SAMPLE_RATE)
    base = _lowpass(_noise(1.4, 0.9, rng), alpha=0.15)
    crackle = _pulses(1.4, 55, 400, 0.7, jitter=0.3)
    out = [0.6 * b + 0.7 * c for b, c in zip(base, crackle)]
    return _normalize(_adsr(out, 0.02, 0.5), 0.8)


def make_sword():
    rng = random.Random(555)
    n = int(0.9 * SAMPLE_RATE)
    out = [0.0] * n
    for f in (2400, 3600, 5100, 7200):
        for i in range(n):
            out[i] += 0.5 * math.sin(2 * math.pi * f * i / SAMPLE_RATE) * math.exp(-i / (n * 0.12))
    clash = _highpass_noise(n, rng)
    for i in range(n):
        out[i] += 0.6 * clash[i] * math.exp(-i / (n * 0.05))
    return _normalize(out, 0.8)


def _highpass_noise(n, rng):
    x = [rng.random() * 2 - 1 for _ in range(n)]
    lo = _lowpass(x, alpha=0.05)
    return [a - b for a, b in zip(x, lo)]


def make_splash():
    rng = random.Random(989)
    n = int(0.9 * SAMPLE_RATE)
    noise = _bandpass(_noise(0.9, 1.0, rng), alpha=0.08)
    out = []
    for i in range(n):
        out.append(noise[i] * math.exp(-i / (n * 0.28)))
    out += _thud(90, 0.06, 0.5)
    return _normalize(out, 0.8)


def make_wolf():
    rng = random.Random(414)
    howl = _chirp(280, 620, 0.8, 0.8) + _chirp(620, 340, 0.9, 0.7)
    growl = _lowpass(_noise(1.6, 0.6, rng), alpha=0.06)
    out = list(howl)
    for i, g in enumerate(growl):
        if i < len(out):
            out[i] += 0.3 * g * (i / len(growl))
    return _normalize(_adsr(out, 0.05, 0.4), 0.8)


def make_roar():
    rng = random.Random(902)
    n = int(2.2 * SAMPLE_RATE)
    out = [0.0] * n
    for i in range(n):
        t = i / n
        f = 70 + 40 * math.sin(2 * math.pi * 5 * t)
        env = math.sin(math.pi * min(1.0, t * 1.2)) * math.exp(-0.3 * t)
        out[i] = 0.8 * env * math.sin(2 * math.pi * f * i / SAMPLE_RATE)
    noise = _lowpass(_noise(2.2, 1.0, rng), alpha=0.03)
    for i in range(n):
        out[i] += 0.5 * noise[i] * math.exp(-i / (n * 0.4))
    return _normalize(out, 0.85)


def make_stone():
    rng = random.Random(616)
    n = int(1.1 * SAMPLE_RATE)
    out = [0.0] * n
    for _ in range(9):
        f = rng.uniform(900, 2600)
        ln = int(rng.uniform(0.03, 0.09) * SAMPLE_RATE)
        pos = int(rng.uniform(0, 0.8) * SAMPLE_RATE)
        for j in range(ln):
            if pos + j < n:
                out[pos + j] += 0.5 * math.sin(2 * math.pi * f * j / SAMPLE_RATE) * math.exp(-j / (ln * 0.25))
    return _normalize(out, 0.7)


def make_magic():
    n = int(1.3 * SAMPLE_RATE)
    out = [0.0] * n
    for f, amp in ((880, 0.4), (1174.66, 0.3), (1568, 0.25), (2093, 0.18), (2637, 0.12)):
        for i in range(n):
            out[i] += amp * math.sin(2 * math.pi * f * i / SAMPLE_RATE) * math.exp(-i / (n * 0.5))
    shimmer = _pulses(1.3, 30, 5200, 0.2, jitter=0.1)
    for i in range(n):
        out[i] += shimmer[i] * math.exp(-i / (n * 0.6))
    return _normalize(_adsr(out, 0.01, 0.4), 0.75)


def make_whisper():
    rng = random.Random(303)
    n = int(1.3 * SAMPLE_RATE)
    noise = _bandpass(_noise(1.3, 0.9, rng), alpha=0.25)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # a few "syllables" of breath
        syl = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(2 * math.pi * 6.5 * t))
        out.append(noise[i] * syl)
    return _normalize(_adsr(out, 0.05, 0.3), 0.7)


def make_creak():
    rng = random.Random(721)
    n = int(0.9 * SAMPLE_RATE)
    creak = _chirp(160, 70, 0.9, 0.8)
    wood = _bandpass(_noise(0.9, 0.5, rng), alpha=0.08)
    out = [c + 0.3 * w for c, w in zip(creak, wood)]
    return _normalize(_adsr(out, 0.02, 0.2), 0.7)


def make_gasp():
    rng = random.Random(149)
    n = int(0.5 * SAMPLE_RATE)
    noise = _bandpass(_noise(0.5, 0.9, rng), alpha=0.2)
    out = []
    for i in range(n):
        t = i / n
        out.append(noise[i] * math.sin(math.pi * t) * (0.4 + 0.6 * t))
    return _normalize(out, 0.8)


def make_chains():
    rng = random.Random(858)
    n = int(1.1 * SAMPLE_RATE)
    out = [0.0] * n
    for _ in range(7):
        f = rng.uniform(1800, 4200)
        ln = int(rng.uniform(0.02, 0.06) * SAMPLE_RATE)
        pos = int(rng.uniform(0, 0.8) * SAMPLE_RATE)
        for j in range(ln):
            if pos + j < n:
                out[pos + j] += 0.5 * math.sin(2 * math.pi * f * j / SAMPLE_RATE) * math.exp(-j / (ln * 0.2))
    rattle = _bandpass(_noise(0.4, 0.5, rng), alpha=0.15)
    _mix_into(out, [0.5 * x for x in rattle], int(0.3 * SAMPLE_RATE))
    return _normalize(out, 0.75)



AUDIO_BUILDERS = {
    "farm_ambient.wav": make_farm_ambient,
    "road_ambient.wav": make_road_ambient,
    "village_ambient.wav": make_village_ambient,
    "mountain_ambient.wav": make_mountain_ambient,
    "wood_ambient.wav": make_wood_ambient,
    "castle_ambient.wav": make_castle_ambient,
    "spire_ambient.wav": make_spire_ambient,
    "action_run.wav": make_run,
    "action_gallop.wav": make_gallop,
    "action_scream.wav": make_scream,
    "action_steps.wav": make_steps,
    "action_door.wav": make_door,
    "action_fire.wav": make_fire,
    "action_sword.wav": make_sword,
    "action_splash.wav": make_splash,
    "action_wolf.wav": make_wolf,
    "action_roar.wav": make_roar,
    "action_stone.wav": make_stone,
    "action_magic.wav": make_magic,
    "action_whisper.wav": make_whisper,
    "action_creak.wav": make_creak,
    "action_gasp.wav": make_gasp,
    "action_chains.wav": make_chains,
    "death_bell.wav": make_bell,
}


# --------------------------------------------------------------------------
# illustration drawing (flat fairytale placeholder style)
# --------------------------------------------------------------------------

SKY_DAY = (138, 184, 222)
SKY_DUSK = (128, 108, 142)
SKY_DARK = (34, 34, 48)
GRASS = (98, 150, 78)
GRASS_DARK = (66, 108, 60)
DIRT = (176, 146, 106)


def _sky(surf, color, horizon=0.62):
    pygame.draw.rect(surf, color, (0, 0, W, int(H * horizon)))


def _ground(surf, color, horizon=0.62):
    pygame.draw.rect(surf, color, (0, int(H * horizon), W, H - int(H * horizon)))


def _sun(surf, x, y, r=34):
    pygame.draw.circle(surf, (250, 208, 92), (x, y), r)
    pygame.draw.circle(surf, (255, 236, 160), (x, y), r - 6)


def _house(surf, x, y, w=120, h=90):
    pygame.draw.rect(surf, (206, 190, 160), (x, y + h // 2, w, h // 2))
    pygame.draw.polygon(surf, (122, 72, 46),
                        [(x - 12, y + h // 2), (x + w // 2, y), (x + w + 12, y + h // 2)])
    pygame.draw.rect(surf, (80, 52, 36), (x + w // 2 - 10, y + h // 2 + 20, 20, h // 2 - 20))
    pygame.draw.rect(surf, (150, 180, 210), (x + 18, y + h // 2 + 12, 18, 18))


def _farmer(surf, x, y, s=1.0):
    p = CHARACTERS["farmer"]["palette"]
    pygame.draw.rect(surf, p["trousers"], (int(x - 7 * s), int(y + 14 * s), int(6 * s), int(12 * s)))
    pygame.draw.rect(surf, p["trousers"], (int(x + 1 * s), int(y + 14 * s), int(6 * s), int(12 * s)))
    pygame.draw.rect(surf, p["tunic"], (int(x - 13 * s), int(y + 4 * s), int(5 * s), int(10 * s)))
    pygame.draw.rect(surf, p["tunic"], (int(x + 8 * s), int(y + 4 * s), int(5 * s), int(10 * s)))
    pygame.draw.rect(surf, p["tunic"], (int(x - 8 * s), int(y + 2 * s), int(16 * s), int(14 * s)))
    pygame.draw.circle(surf, p["skin"], (int(x), int(y - 3 * s)), int(6 * s))
    pygame.draw.rect(surf, p["hair"], (int(x - 6 * s), int(y - 9 * s), int(12 * s), int(4 * s)))


def _chicken(surf, x, y):
    pygame.draw.ellipse(surf, (232, 224, 200), (x, y, 18, 14))
    pygame.draw.circle(surf, (232, 224, 200), (x + 14, y - 2), 8)
    pygame.draw.polygon(surf, (224, 150, 40), [(x + 20, y - 2), (x + 28, y), (x + 20, y + 3)])
    pygame.draw.rect(surf, (224, 150, 40), (x + 8, y + 13, 3, 8))


def _sheep(surf, x, y):
    for ox in (-10, 0, 10):
        pygame.draw.circle(surf, (236, 236, 230), (x + ox, y + (8 if ox else 0)), 12)
    pygame.draw.ellipse(surf, (52, 48, 44), (x - 8, y - 12, 16, 12))
    pygame.draw.rect(surf, (52, 48, 44), (x - 5, y + 12, 3, 10))
    pygame.draw.rect(surf, (52, 48, 44), (x + 3, y + 12, 3, 10))


def _spire(surf, x, y, h=200):
    color = (44, 44, 58)
    base_w = 46
    pygame.draw.rect(surf, color, (x - base_w // 2, y - h, base_w, h))
    pygame.draw.polygon(surf, color, [(x - base_w // 2, y - h), (x, y - h - 70),
                                      (x + base_w // 2, y - h)])
    pygame.draw.rect(surf, (200, 150, 60), (x - 4, y - h + 30, 8, 16))


def _mountain(surf, x, y, w=180, h=160):
    pygame.draw.polygon(surf, (120, 120, 134), [(x - w // 2, y), (x, y - h), (x + w // 2, y)])


def _tree(surf, x, y, h=90):
    pygame.draw.rect(surf, (60, 40, 30), (x - 4, y - h // 2, 8, h // 2))
    pygame.draw.polygon(surf, (34, 52, 40), [(x, y - h), (x - 30, y - h // 3), (x + 30, y - h // 3)])
    pygame.draw.polygon(surf, (34, 52, 40), [(x, y - int(h * 0.75)),
                                             (x - 24, y - h // 4), (x + 24, y - h // 4)])


def _torch(surf, x, y):
    pygame.draw.rect(surf, (90, 60, 34), (x - 2, y, 5, 30))
    pygame.draw.circle(surf, (240, 150, 50), (x, y - 4), 10)
    pygame.draw.circle(surf, (255, 210, 90), (x, y - 4), 5)


def draw_farm():
    s = pygame.Surface(SIZE)
    _sky(s, SKY_DAY)
    _ground(s, GRASS)
    _sun(s, 420, 70)
    _house(s, 60, 240)
    for fx in range(200, 440, 28):
        pygame.draw.rect(s, (150, 110, 70), (fx, 320, 6, 30))
    pygame.draw.rect(s, (150, 110, 70), (196, 326, 260, 6))
    _farmer(s, 300, 330, s=1.6)
    _chicken(s, 250, 360)
    _sheep(s, 385, 350)
    return s


def draw_errand():
    s = pygame.Surface(SIZE)
    _sky(s, SKY_DAY)
    _ground(s, DIRT)
    _sun(s, 420, 70)
    pygame.draw.polygon(s, (196, 170, 130), [(210, 512), (300, 512), (290, 280), (240, 280)])
    for vx in (60, 130, 200, 340, 400, 450):
        pygame.draw.polygon(s, (150, 60, 48), [(vx, 317), (vx + 30, 317), (vx + 15, 285)])
    pygame.draw.circle(s, (120, 90, 60), (285, 425), 9)  # sack
    _farmer(s, 256, 430, s=1.4)
    return s


def draw_return():
    s = pygame.Surface(SIZE)
    _sky(s, (108, 116, 140))
    _ground(s, GRASS_DARK)
    _house(s, 60, 240)
    pygame.draw.rect(s, (30, 24, 20), (108, 300, 26, 52))  # open dark doorway
    _farmer(s, 320, 360, s=1.3)
    return s


def draw_road():
    s = pygame.Surface(SIZE)
    _sky(s, SKY_DUSK)
    _ground(s, (96, 100, 104))
    _spire(s, 256, 300, h=190)
    _mountain(s, 90, 320, 170, 150)
    _tree(s, 430, 320, 90)
    _tree(s, 470, 320, 70)
    pygame.draw.polygon(s, (130, 110, 84), [(230, 512), (300, 512), (300, 340), (270, 340)])
    pygame.draw.polygon(s, (90, 76, 58), [(300, 512), (380, 512), (330, 330)])
    _farmer(s, 250, 420, s=1.1)
    return s


def draw_death():
    s = pygame.Surface(SIZE)
    _sky(s, SKY_DARK)
    _ground(s, (24, 24, 32))
    pygame.draw.polygon(s, (10, 10, 16), [(150, 320), (360, 320), (300, 512), (200, 512)])
    for rx, ry, rr in [(190, 360, 12), (320, 400, 9), (260, 450, 14)]:
        pygame.draw.circle(s, (60, 60, 70), (rx, ry), rr)
    p = CHARACTERS["farmer"]["palette"]
    pygame.draw.rect(s, p["tunic"], (249, 348, 14, 12))
    pygame.draw.circle(s, p["skin"], (261, 342), 6)
    pygame.draw.rect(s, p["trousers"], (247, 358, 6, 10))
    pygame.draw.rect(s, p["trousers"], (259, 358, 6, 10))
    return s


def draw_castle():
    s = pygame.Surface(SIZE)
    _sky(s, (46, 46, 66))
    _ground(s, (60, 60, 74))
    _spire(s, 256, 300, h=230)
    pygame.draw.rect(s, (96, 96, 110), (120, 300, 272, 212))
    pygame.draw.rect(s, (66, 66, 80), (120, 300, 272, 40))
    pygame.draw.rect(s, (70, 44, 30), (210, 340, 92, 172))
    pygame.draw.line(s, (40, 26, 18), (256, 340), (256, 512), 3)
    _torch(s, 180, 360)
    _torch(s, 332, 360)
    _farmer(s, 150, 470, s=0.9)
    return s


IMAGE_BUILDERS = {
    "farm": draw_farm,
    "errand": draw_errand,
    "return": draw_return,
    "road": draw_road,
    "death": draw_death,
    "castle": draw_castle,
}


def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    pygame.init()

    print("Generating audio...")
    for name, build in AUDIO_BUILDERS.items():
        path = os.path.join(AUDIO_DIR, name)
        samples = build()
        _write(path, samples)
        print("  %-20s %.1fs  %d bytes" % (name, len(samples) / SAMPLE_RATE, os.path.getsize(path)))

    print("Generating images...")
    for name, build in IMAGE_BUILDERS.items():
        path = os.path.join(IMAGE_DIR, name + ".png")
        surf = build()
        pygame.image.save(surf, path)
        print("  %-20s %s  %d bytes" % (name + ".png", surf.get_size(), os.path.getsize(path)))

    print("Done.")


if __name__ == "__main__":
    main()
