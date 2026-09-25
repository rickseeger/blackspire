"""Report the Black Spire scene/choice-to-audio map and write it to disk.

Run from the repo root:

    .venv/bin/python tools/report_audio.py            # print to stdout
    .venv/bin/python tools/report_audio.py --write    # also write docs/audio_map.txt + .json

This is the node-4 evidence artifact: for every scene the always-on ambient
bed, and for every choice the one-shot action sound it triggers.  It also
validates that every ambient id and every action-sound id resolves to a real
asset and that the story graph is sound.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from black_spire import audio, story


def build_map():
    scenes = []
    for sid, sc in story.SCENES.items():
        choices = [
            {
                "index": i,
                "label": c.label,
                "target": c.target,
                "action_sound": c.action_sound,
                "action_file": audio.ACTIONS.get(c.action_sound),
            }
            for i, c in enumerate(sc.choices)
        ]
        scenes.append({
            "scene_id": sid,
            "title": sc.title,
            "kind": sc.kind,
            "ambient": sc.ambient,
            "ambient_file": audio.AMBIENTS.get(sc.ambient),
            "choices": choices,
        })
    return {
        "start_scene": story.START_SCENE,
        "death_bell": story.DEATH_BELL,
        "death_bell_file": audio.ACTIONS.get(story.DEATH_BELL),
        "scenes": scenes,
    }


def render_text(data):
    lines = []
    lines.append("Black Spire - scene/choice-to-audio map")
    lines.append("=" * 60)
    lines.append("start scene : %s" % data["start_scene"])
    lines.append("death bell  : %s -> %s" % (data["death_bell"], data["death_bell_file"]))
    lines.append("")

    # group scenes by ambient bed
    by_ambient = {}
    for sc in data["scenes"]:
        by_ambient.setdefault(sc["ambient"], []).append(sc)

    lines.append("AMBIENT BEDS (always-on, looped per scene)")
    lines.append("-" * 60)
    for amb, scs in sorted(by_ambient.items()):
        fname = audio.AMBIENTS.get(amb)
        ids = ", ".join(s["scene_id"] for s in scs)
        lines.append("  %-9s %-20s %d scene(s): %s" % (amb, fname, len(scs), ids))
    lines.append("")

    lines.append("SCENES AND THEIR CHOICES")
    lines.append("-" * 60)
    for sc in data["scenes"]:
        tag = " [%s]" % sc["kind"].upper() if sc["kind"] != "scene" else ""
        lines.append("[%s]%s %s" % (sc["scene_id"], tag, sc["title"]))
        lines.append("    ambient: %s (%s)" % (sc["ambient"], sc["ambient_file"]))
        for c in sc["choices"]:
            lines.append("      %d. %-44s -> %-18s sound=%-9s (%s)"
                         % (c["index"] + 1, c["label"], c["target"],
                            c["action_sound"], c["action_file"]))
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Black Spire audio-map report")
    parser.add_argument("--write", action="store_true",
                        help="also write docs/audio_map.txt + .json")
    args = parser.parse_args(argv)

    data = build_map()
    text = render_text(data)

    problems = story.validate_graph() + audio.validate_audio(story.SCENES)
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  - " + p)
        return 1

    print(text)

    if args.write:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs = os.path.join(root, "docs")
        os.makedirs(docs, exist_ok=True)
        txt_path = os.path.join(docs, "audio_map.txt")
        json_path = os.path.join(docs, "audio_map.json")
        with open(txt_path, "w") as f:
            f.write(text + "\n")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
        print("wrote %s" % os.path.relpath(txt_path, root))
        print("wrote %s" % os.path.relpath(json_path, root))

    print("")
    print("OK: %d scenes, %d ambients, %d actions all resolve; graph valid"
          % (len(data["scenes"]), len(audio.AMBIENTS), len(audio.ACTIONS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
