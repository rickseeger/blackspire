"""Regenerate the per-scene image manifest (assets/images/manifest.json).

The manifest is the single source of truth mapping scene id -> image filename
under ``assets/images/``.  Node 3 landed the real AI art set: one gpt-image-1
illustration per scene id (``<scene_id>.png``, a 512x512 engine copy, with the
1024x1024 originals kept under ``assets/images/originals/``).  The engine and
story data are untouched; this tool only rewrites the manifest.

Run from the repo root:

    .venv/bin/python tools/generate_image_manifest.py            # write manifest.json
    .venv/bin/python tools/generate_image_manifest.py --check    # verify only

The ``--check`` mode fails (exit 1) if the on-disk manifest is out of sync with
the story graph, which keeps the committed manifest honest in CI.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from black_spire import art, story  # noqa: E402


def build_manifest():
    return {
        "format": "blackspire-image-manifest",
        "version": 2,
        "note": (
            "Per-scene illustration manifest, keyed by scene id -> image filename "
            "under assets/images/.  Node 3 landed the real AI art set: one "
            "gpt-image-1 illustration per scene id, with the 1024x1024 originals "
            "under assets/images/originals/."
        ),
        "default": "farm.png",
        "scenes": {
            sid: "%s.png" % sid
            for sid in story.SCENES
        },
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate the Black Spire image manifest")
    ap.add_argument("--check", action="store_true",
                    help="verify the on-disk manifest is in sync and exit")
    args = ap.parse_args(argv)

    data = build_manifest()

    if args.check:
        if not os.path.exists(art.MANIFEST_PATH):
            print("manifest missing: %s" % art.MANIFEST_PATH, file=sys.stderr)
            return 1
        with open(art.MANIFEST_PATH, "r", encoding="utf-8") as f:
            on_disk = json.load(f)
        if on_disk.get("scenes") != data["scenes"]:
            print("manifest out of sync with story graph; re-run "
                  "tools/generate_image_manifest.py", file=sys.stderr)
            return 1
        problems = art.validate_image_manifest(story.SCENES)
        if problems:
            for p in problems:
                print("  - " + p, file=sys.stderr)
            return 1
        print("manifest in sync: %d scenes, all image files present"
              % len(data["scenes"]))
        return 0

    os.makedirs(os.path.dirname(art.MANIFEST_PATH), exist_ok=True)
    with open(art.MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print("wrote %s (%d scenes)" % (art.MANIFEST_PATH, len(data["scenes"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
