# Black Spire

A sound-centric fairytale choose-your-own-adventure.  This repository is the
cheap proof-of-concept *vertical slice*: a windowed Python app covering the
opening scenes end-to-end, to prove the engine (window, story graph, choice
navigation, image rendering, layered audio) before scaling to ~60 scenes.

## The story (slice)

You are a poor farmer in a fairytale land of wizards and dragons.  You return
home from an errand to learn the queen has died and the king, seeking a new
queen, has taken the most beautiful woman in the village - your wife - and
carried her to the castle at the Black Spire.  You set out to bring her back.

The slice covers the farm, the errand, the return home, and the road toward
the castle, with one real fork: the high mountain path (death) or the low road
through the wood (continuation).  It plays start-to-finish in under two
minutes.

## Sound is the heart

* One always-on ambient bed per scene (chickens and sheep at the farm; wind
  and distant hooves on the road).
* One-shot action sounds layered on top when a choice plays out: running
  footsteps, a horse galloping, a scream on the fall.
* A single large death bell tolls on the one death scene.

All audio is procedurally generated (stdlib `wave`), so there are no
licensing concerns and the files stay small.

## Install and run (one command)

    git clone git@github.com:rickseeger/blackspire.git
    cd blackspire
    ./launch.sh

`launch.sh` creates a local `.venv`, installs the single dependency
(pygame-ce, the actively maintained pygame - same `import pygame`), and
launches the window.  If you prefer to drive it yourself:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    python3 -m black_spire        # or: python3 main.py

Controls: press 1-9 or click a choice, ESC to quit.

## Headless / CI flags

    python3 -m black_spire --list            # print the scene graph
    python3 -m black_spire --frames 30       # open, run 30 frames, exit
    python3 -m black_spire --scene road      # start at a specific scene

The app is headless-safe: with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`
it initializes, renders, and exits cleanly (used by the smoke test).

## Smoke test

    ./test.sh

Runs headless and asserts: no dead ends (every choice resolves to a valid
scene), a continuation path and a death path both exist, the death scene tolls
the bell exactly once, scene text renders next to the illustration, the farmer
is defined in the character sheet and the farm picture contains his tunic
color, and every sound asset loads with non-zero length.

## Layout

    black_spire/          the app package (python3 -m black_spire)
      story.py            data-driven scene graph + pure story engine
      characters.py       character sheet (written description + palette)
      audio.py            layered audio (ambient bed / actions / death bell)
      art.py              illustration loader
      app.py              pygame window, layout, input, main loop
    assets/audio/         procedurally generated wavs
    assets/images/        flat placeholder illustrations (png)
    tools/generate_assets.py   regenerates all audio + images from scratch
    tests/test_smoke.py        automated smoke test

Art is intentionally low-effort placeholder in one consistent style - node 3
owns the real art set.  Visual and sound *quality* are deferred to Rick's
playtest, not gated here.
