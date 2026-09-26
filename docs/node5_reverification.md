# Black Spire — Node 5 Re-verification Report (G18)

Re-verified the complete Black Spire game against the NEW real audio (node 4's
Wikimedia Commons recordings). Node 5's earlier integration verification ran
against the old synthesized beeps and was stale; this report supersedes it.

Everything below was produced from a clean `git clone
git@github.com:rickseeger/blackspire.git` at commit `eaebafc`, on Linux
(Python 3.14.4, pygame-ce 2.5.8), with ffmpeg/ffprobe available.

## Results (all pass)

1. Clean-checkout, one-command run
   - `./launch.sh --frames 30` (headless) -> exit 0: the window opens, runs,
     and exits cleanly from a fresh checkout with one command.
   - `python3 -m black_spire --list` -> 68 scenes enumerated with titles,
     choices, targets, and per-choice action sounds.

2. Automated path-walk suite (green)
   - `python3 -m unittest discover -s tests -v` -> Ran 65 tests, OK
     (0 failures, ~19s). Full output saved alongside this report as
     test_output.txt.

3. Story graph
   - 68 scenes, 125 choices, 15 death endings, 4 good endings.
   - Every choice resolves to a valid scene id (no dangling edges).
   - All 68 scenes reachable from the start; all 15 death endings and all 4
     good endings reachable (confirmed by the exhaustive edge-covering walk
     and by tools/playthrough.py, which prints a concrete path to each).

4. Audio — the node-4 change, now real recordings
   - 24 WAV files on disk == 24 sound ids (7 ambient beds + 16 action
     one-shots + 1 death bell).
   - Every file is a genuine RIFF/WAVE recording with a recorded Wikimedia
     Commons source URL + license in docs/audio_sources.json (24/24).
   - No dangling references to any old synthesized path: a full-tree scan for
     `.wav` names found every mentioned basename on disk; the only non-disk
     match was a URL fragment inside docs/audio_sources.json, not a code ref.
   - Every file is non-silent (ffmpeg volumedetect) with positive duration;
     ambient beds are >= 5s.
   - Ambient beds peak below action one-shots (mix layering correct:
     AMBIENT_VOLUME 0.55 < ACTION_VOLUME 0.9).

5. Art
   - 68 engine PNGs (512x512) + 68 originals (1024x1024), manifest wired 1:1
     with no orphans.
   - Every scene renders a non-blank frame; per-scene color-diversity checks
     pass (real AI art, not flat placeholders).

6. Death bell
   - Wired. Exactly one toll on every death scene, zero tolls on every good
     ending.

## Conclusion

The game is ready to re-hand to Rick for playtest of story coherence, art
beauty, and sound quality. Note for Rick: the audio is now real recordings
(Wikimedia Commons CC0 / public domain / CC-BY), not synthesized beeps.

Verification date: 2026-09-26 UTC
Commit under test: eaebafc
