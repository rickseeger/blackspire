# Black Spire

A sound-centric fairytale choose-your-own-adventure.  You are a poor farmer
whose wife has been taken by the king, and you walk to the Black Spire to bring
her home.  This repository now carries the **complete** story: ~68 scenes of
plain young-adult prose, many ways to die, and several distinct good endings,
driven by a data-driven story graph and a layered audio engine.

## The story

The queen is dead.  The king, needing a new queen, has taken the most beautiful
woman in the village - your wife, Lena - and carried her to the castle at the
Black Spire.  You set out to bring her back.

The road forks: a high mountain path (a crumbling ledge, the wizard's hut, and
a dragon across the pass) or a dark wood (will-o'-the-wisps, a black river, and
a wolf pack).  Both roads meet at the castle gate, and both lead up the winding
stair to the Spire, where Lena is held behind the king's spell - a stolen
dragon-fire that keeps the king's power alive.

There are many ways to die: a fall, a dragon's flame, the bog, the river, the
wolves, the guards' swords, the wall, despair in the dungeon, the king's spell,
and the king himself.  And there are several distinct good endings:

* **Punish the king** - you fight him and he falls.
* **Prevent it from happening again** - you quench the stolen fire and write a
  new law into the land, so no king may ever take a bride by force again.
* **Escape together** - you and Lena run, and never look back.
* **Free the dragon** - you break the king's hold on the fire, and the dragon
  turns on him and flies free.

Every choice leads to a coherent next beat; there are no dangling threads.  Run
`tools/report_story.py --write` for a full scene/choice/ending report.

### The cast

The story keeps a fixed cast, each with a one-line description in
`black_spire/characters.py`: the farmer (you), Lena (your wife), the king, the
wizard, the dragon, the old woman at the village, the neighbor, the guard
captain, the serving girl, and the queen's ghost.

## Sound is the heart

* One always-on ambient bed per scene (chickens and sheep at the farm; wind and
  distant hooves on the road; silence in the death scenes).
* One-shot action sounds layered on top when a choice plays out: running
  footsteps, a horse galloping, a scream on a fall.
* A single large death bell tolls on every death scene.

All audio is procedurally generated (stdlib `wave`), so there are no licensing
concerns and the files stay small.

## Install and run (one command)

    git clone git@github.com:rickseeger/blackspire.git
    cd blackspire
    ./launch.sh

`launch.sh` creates a local `.venv`, installs the single dependency
(pygame-ce, the actively maintained pygame - same `import pygame`), and launches
the window.  If you prefer to drive it yourself:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    python3 -m black_spire        # or: python3 main.py

Controls: press 1-9 or click a choice, ESC to quit.

## Headless / CI flags

    python3 -m black_spire --list            # print the scene graph (marks endings)
    python3 -m black_spire --frames 30       # open, run 30 frames, exit
    python3 -m black_spire --scene road      # start at a specific scene

The app is headless-safe: with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`
it initializes, renders, and exits cleanly (used by the smoke test).

## Smoke test

    ./test.sh

Runs headless and asserts: the graph is valid (no dangling choices), >= 60
scenes, many death endings and several good endings, 2-4 choices per non-terminal
scene, every choice resolves to a valid scene, every scene and every ending is
reachable from the start, the three required good endings are present, a death
path tolls the bell exactly once, a good-ending path never tolls it, scene text
renders next to the illustration, the farmer matches his written description,
and every sound asset loads with non-zero length.

## Story report

    .venv/bin/python tools/report_story.py            # print to stdout
    .venv/bin/python tools/report_story.py --write    # also write docs/story_report.txt

Walks the graph from the start and reports scene/choice counts, edge integrity,
reachability of every scene and ending, and a concrete path to each ending.

## Layout

    black_spire/          the app package (python3 -m black_spire)
      story.py            data-driven story graph (~68 scenes) + pure story engine
      characters.py       character sheet (one-line descriptions + palettes)
      audio.py            layered audio (ambient bed / actions / death bell)
      art.py              illustration loader
      app.py              pygame window, layout, input, main loop
    assets/audio/         procedurally generated wavs
    assets/images/        flat placeholder illustrations (png)
    tools/generate_assets.py   regenerates all audio + images from scratch
    tools/report_story.py      scene/choice/ending report + reachability walk
    docs/story_report.txt      generated story report
    tests/test_smoke.py        automated smoke test

Art is intentionally low-effort placeholder in one consistent style - a later
node owns the real art set.  Visual and sound *quality* are deferred to the
human playtest, not gated here.
