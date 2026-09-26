"""Character-sheet + illustration consistency checks for Black Spire (node 8).

The node-3 art set locks every recurring character to ONE fixed written
description (``docs/character_sheet.md``) and injects that exact text verbatim
into every scene prompt the character appears in (``docs/image_prompts.json``).
This module verifies that contract holds, at the code level only -- there is no
image-perception tool in play:

  * the character sheet is well-formed: every recurring cast member has exactly
    one fixed, non-empty written description
  * every story scene lists which recurring characters appear in it
    (``docs/scene_characters.json``), and each listed character is a known cast
    member with no duplicate or orphan entries
  * for every scene, the recorded prompt's ``Characters:`` block is byte-for-byte
    the fixed descriptions of exactly the characters listed for that scene -- so
    the same person renders identically in every scene they appear in
  * no cast member is orphaned (every character appears in at least one scene)

``validate_consistency`` folds in ``art.validate_image_manifest`` too, so it
answers "is every scene's final illustration wired and is the cast consistent"
in one call.  Subjective art *quality* remains the human playtester's call.
"""

import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")
CHARACTER_SHEET_PATH = os.path.join(DOCS_DIR, "character_sheet.md")
SCENE_CHARACTERS_PATH = os.path.join(DOCS_DIR, "scene_characters.json")
IMAGE_PROMPTS_PATH = os.path.join(DOCS_DIR, "image_prompts.json")

# The recurring cast: canonical key -> the ``##`` heading used in the sheet.
# This is the fixed cast order the story and the art both share.
CHARACTER_HEADINGS = {
    "farmer": "The Farmer (you)",
    "wife": "Lena (the farmer's wife)",
    "king": "King Aldric",
    "wizard": "The Wizard",
    "dragon": "The Dragon",
    "herald": "The Old Woman",
    "neighbor": "The Neighbor",
    "captain": "The Guard Captain",
    "servant": "The Serving Girl",
    "queen_ghost": "The Queen's Ghost",
}

# The prompt layout is "<style>\n\nScene: ...\n\nCharacters: <block>\n\nMood ...".
_CHARACTERS_RE = re.compile(r"\n\nCharacters: (.*?)\n\nMood and lighting:", re.DOTALL)


def load_character_sheet(path=CHARACTER_SHEET_PATH):
    """Return ``{character_key: fixed_written_description}`` from the sheet.

    The description is the full ``"Name: ..."`` sentence that is injected
    verbatim into prompts (header prefix included), not just the body.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    by_heading = {}
    current = None
    buf = []
    for line in lines:
        if line.startswith("## "):
            if current is not None and buf:
                by_heading[current] = " ".join(buf)
            current = line[3:].strip()
            buf = []
        elif current is not None and line.strip() and not line.strip().startswith(">"):
            buf.append(line.strip())
    if current is not None and buf:
        by_heading[current] = " ".join(buf)

    sheet = {}
    for key, heading in CHARACTER_HEADINGS.items():
        if heading in by_heading:
            sheet[key] = by_heading[heading]
    return sheet


def load_scene_characters(path=SCENE_CHARACTERS_PATH):
    """Return ``{scene_id: [character_key, ...]}`` (which cast appears where)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_image_prompts(path=IMAGE_PROMPTS_PATH):
    """Return ``{scene_id: {prompt: ..., ...}}`` (the recorded node-3 prompts)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("scenes", {})


def characters_block(prompt):
    """Extract the ``Characters:`` block from a recorded prompt, or None."""
    match = _CHARACTERS_RE.search(prompt)
    return match.group(1) if match else None


def validate_character_consistency(scenes=None):
    """Return a list of problems; an empty list means the cast is consistent.

    ``scenes`` is a mapping of scene id -> scene (defaults to ``story.SCENES``);
    only its keys are used.
    """
    from . import story

    if scenes is None:
        scenes = story.SCENES

    problems = []
    sheet = load_character_sheet()
    scene_chars = load_scene_characters()
    prompts = load_image_prompts()

    # 1. The sheet must carry every recurring character, with a real description.
    for key, heading in CHARACTER_HEADINGS.items():
        if key not in sheet:
            problems.append("character sheet missing %r (## %s)" % (key, heading))
            continue
        desc = sheet[key]
        if not desc or not desc.endswith("."):
            problems.append("character sheet %r has an empty/malformed description" % key)

    # 2. The scene->characters map must cover the story and only name known cast.
    scene_ids = set(scenes)
    sc_ids = set(scene_chars)
    for sid in sorted(scene_ids - sc_ids):
        problems.append("scene %r has no character list in scene_characters.json" % sid)
    for sid in sorted(sc_ids - scene_ids):
        problems.append("scene_characters.json references unknown scene %r" % sid)
    for sid, chars in scene_chars.items():
        if sid not in scene_ids:
            continue
        if not isinstance(chars, list) or not chars:
            problems.append("scene %r has an empty character list" % sid)
            continue
        if len(set(chars)) != len(chars):
            problems.append("scene %r lists duplicate characters" % sid)
        for key in chars:
            if key not in CHARACTER_HEADINGS:
                problems.append("scene %r lists unknown character %r" % (sid, key))

    # 3. Every scene must have a recorded prompt, and no orphan prompts.
    prompt_ids = set(prompts)
    for sid in sorted(scene_ids - prompt_ids):
        problems.append("scene %r has no recorded image prompt" % sid)
    for sid in sorted(prompt_ids - scene_ids):
        problems.append("image_prompts.json references unknown scene %r" % sid)

    # 4. Verbatim injection: each scene's Characters block is exactly the fixed
    #    descriptions of the characters listed for that scene, in order.
    for sid in sorted(scene_ids):
        if sid not in prompts or sid not in scene_chars:
            continue
        chars = scene_chars[sid]
        if not all(key in sheet for key in chars):
            continue  # unknown character already reported above
        block = characters_block(prompts[sid].get("prompt", ""))
        if block is None:
            problems.append("scene %r prompt has no 'Characters:' block" % sid)
            continue
        expected = " ".join(sheet[key] for key in chars)
        if block != expected:
            problems.append(
                "scene %r Characters block does not match the fixed sheet "
                "(drift, or a missing/extra character)" % sid)

    # 5. No orphan cast member: every character appears in at least one scene.
    used = set()
    for chars in scene_chars.values():
        used.update(chars)
    for key in CHARACTER_HEADINGS:
        if key not in used:
            problems.append("character %r appears in no scene" % key)

    return problems


def validate_consistency(scenes=None):
    """Combined illustration-wiring + character-sheet consistency problems."""
    from . import art, story

    if scenes is None:
        scenes = story.SCENES
    return art.validate_image_manifest(scenes) + validate_character_consistency(scenes)
