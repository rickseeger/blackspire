"""Generate the Black Spire fairytale illustration set (node 3).

Every scene's illustration is produced with the OpenAI Images API
(``gpt-image-1``, 1024x1024), decoded from the API's base64 PNG, then a 512x512
copy is written for the engine (``art.ILLUSTRATION_SIZE`` is 512x512).  The
genuine 1024x1024 outputs are kept under ``assets/images/originals/``.

The locked style (fixed by Rick) and the fixed character sheet are embedded
below.  Each recurring character has ONE fixed written description, injected
verbatim into every scene prompt they appear in, so the same person renders
identically in every illustration.

Run from the repo root:

    set -a; source /root/.hermes/.env; set +a   # or export OPENAI_API_KEY
    python3 tools/generate_artset.py --workers 4
    python3 tools/generate_artset.py --check      # verify the on-disk set

Artifacts written:
    assets/images/originals/<scene_id>.png   1024x1024 genuine API output
    assets/images/<scene_id>.png             512x512 engine copy
    assets/images/manifest.json              scene id -> <scene_id>.png
    docs/character_sheet.md                  fixed cast + locked style
    docs/image_prompts.json                  scene id -> prompt + API metadata
"""

import argparse
import base64
import io
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------------------------------------------------------
# Locked style (fixed by Rick).  Injected into EVERY prompt.
# ----------------------------------------------------------------------------
STYLE = (
    "Cinematic digital fantasy painting in a modern game-art style: dramatic "
    "lighting, rich saturated color, moody atmosphere, high detail, painterly "
    "brushwork, strong rim light and volumetric light, deep shadows, an epic "
    "fairytale mood."
)

# ----------------------------------------------------------------------------
# Fixed character sheet.  Each entry is ONE fixed written description; it is
# injected verbatim into every prompt the character appears in.
# ----------------------------------------------------------------------------
CHARACTERS = {
    "farmer": (
        "The Farmer: a wiry man in his forties with sun-browned skin, short "
        "dark brown hair, a weathered kind face and tired eyes, wearing a "
        "patched brown linen tunic, grey-brown trousers and worn leather "
        "boots, with calloused hands."
    ),
    "wife": (
        "Lena the farmer's wife: a gentle, beautiful woman with long dark "
        "brown hair in a single braid, warm eyes and soft features, wearing "
        "a faded blue dress and a white apron dusted with flour."
    ),
    "king": (
        "King Aldric: a tall, gaunt king with pale skin, sharp cold features, "
        "slicked-back black hair and cold grey eyes, wearing long black robes "
        "trimmed in crimson beneath a thin golden crown."
    ),
    "wizard": (
        "The Wizard: a hunched old wizard with a long white beard, deep-set "
        "grey eyes and a weathered wrinkled face, wearing grey robes, leaning "
        "on a gnarled wooden staff."
    ),
    "dragon": (
        "The Dragon: a vast ancient dragon with emerald-green scales and a "
        "pale underbelly, huge leathery wings and golden knowing eyes, with "
        "smoke curling from its nostrils."
    ),
    "herald": (
        "The Old Woman: a bent, frail old woman with white hair and a "
        "weathered wrinkled face, wearing a grey shawl over a dark dress, "
        "leaning on a wooden walking stick."
    ),
    "neighbor": (
        "The Neighbor: a sturdy middle-aged villager with a worried face and "
        "a brown beard, wearing a brown wool coat over a plain linen shirt."
    ),
    "captain": (
        "The Guard Captain: a broad, scarred soldier with a shaved head and "
        "a short beard, grim expression, wearing dark steel armor and a "
        "black cloak."
    ),
    "servant": (
        "The Serving Girl: a quick, kind young serving girl with brown hair "
        "tied back, wearing a linen apron over a simple brown dress, carrying "
        "a tray of bread."
    ),
    "queen_ghost": (
        "The Queen's Ghost: a pale, translucent woman with long dark hair and "
        "sad eyes, wearing a flowing white gown, faint and ethereal with a "
        "soft glow."
    ),
}

# ----------------------------------------------------------------------------
# Per-scene prompt data: title, scene description, characters present, mood.
# ----------------------------------------------------------------------------
SCENES = {
    "farm": {"title": "The Farm",
             "desc": "a humble farmstead at sunrise, a small wooden farmhouse "
                     "and barn, chickens scratching in the dirt and sheep in "
                     "a field, golden morning light",
             "chars": ["farmer"], "mood": "warm golden dawn, peaceful"},
    "animals": {"title": "The Animals",
                "desc": "a farmer scattering grain to the chickens while "
                        "sheep watch from a field beside a wooden farmhouse",
                "chars": ["farmer"], "mood": "calm warm morning light"},
    "farewell": {"title": "Farewell",
                 "desc": "a farmer and his wife sharing a tender goodbye "
                         "inside the doorway of their farmhouse, she brushes "
                         "flour from his sleeve",
                 "chars": ["farmer", "wife"],
                 "mood": "warm intimate interior light"},
    "errand": {"title": "The Errand",
               "desc": "a farmer walking a dusty road toward a village "
                       "market, carrying a basket of eggs",
               "chars": ["farmer"], "mood": "bright midday, village bustle"},
    "herald": {"title": "The Old Woman",
               "desc": "an old woman seizing the arm of a farmer on a village "
                       "road, warning him urgently",
               "chars": ["farmer", "herald"],
               "mood": "tense, overcast, ominous warning"},
    "return": {"title": "Home",
               "desc": "a farmer running home to an open farmhouse door, the "
                       "house empty, a worried neighbor meeting him, "
                       "half-kneaded bread dough on the table inside",
               "chars": ["farmer", "neighbor"],
               "mood": "shocked, cold dusk light"},
    "gather": {"title": "What You Carry",
               "desc": "a farmer gathering his few belongings by lamplight: "
                       "a knife, a loaf of bread, a water skin and an old coat",
               "chars": ["farmer"], "mood": "dim determined interior"},
    "road": {"title": "The Fork in the Road",
             "desc": "a farmer at a fork in a road, a dark castle tower "
                     "rising like a finger against a stormy sky, one path "
                     "climbing a mountain and one sinking into a dark wood",
             "chars": ["farmer"], "mood": "epic ominous twilight"},
    "mountain": {"title": "The Mountain Path",
                 "desc": "a steep narrow mountain path cut into rock, loose "
                         "stones, wind whipping a farmer's coat",
                 "chars": ["farmer"], "mood": "high winds, exposed heights"},
    "mountain_ledge": {"title": "The Narrow Ledge",
                       "desc": "a farmer edging along a ledge no wider than "
                               "his shoulders, mist hiding the valley far below",
                       "chars": ["farmer"], "mood": "vertiginous, cold mist"},
    "mountain_scree": {"title": "Loose Rock",
                       "desc": "a farmer scrambling up a slope of loose broken "
                               "stone that shifts with every step",
                       "chars": ["farmer"], "mood": "precarious, gravel slides"},
    "mountain_fall": {"title": "The Fall",
                      "desc": "a farmer falling from a crumbling mountain "
                              "ledge, stone giving way, the valley below",
                      "chars": ["farmer"], "mood": "dizzying plunge, wind"},
    "mountain_ridge": {"title": "The Ridge",
                       "desc": "a farmer on a mountain ridge between two "
                               "peaks, a thin thread of smoke rising from a "
                               "hut nestled in the rocks, a pass ahead",
                       "chars": ["farmer"], "mood": "clear air, distant hut"},
    "wizard_hut": {"title": "The Wizard's Hut",
                   "desc": "a small crooked hut hung with herbs and bone "
                           "wind-chimes, an old wizard in grey robes standing "
                           "in the doorway facing a farmer",
                   "chars": ["farmer", "wizard"],
                   "mood": "mysterious, warm firelight from the hut"},
    "dragon_pass": {"title": "The Dragon's Pass",
                    "desc": "a wide ledge of scorched stone, a vast green "
                            "dragon lying across the path before a farmer, "
                            "smoke curling from its nostrils",
                    "chars": ["farmer", "dragon"],
                    "mood": "ominous, smoke, waiting"},
    "dragon_parley": {"title": "Parley with the Dragon",
                      "desc": "a vast green dragon watching a farmer without "
                              "moving, one golden eye open, a tense standoff",
                      "chars": ["farmer", "dragon"],
                      "mood": "tense, low thunder, eye contact"},
    "dragon_riddle": {"title": "The Dragon's Riddle",
                      "desc": "a vast green dragon lifting its head to ask a "
                              "riddle of a farmer, its golden eye gleaming",
                      "chars": ["farmer", "dragon"],
                      "mood": "testing, gleaming eye"},
    "dragon_wrong": {"title": "The Dragon's Flame",
                     "desc": "a vast green dragon opening its jaws, fire "
                             "erupting toward a farmer on scorched stone",
                     "chars": ["farmer", "dragon"],
                     "mood": "inferno, blinding fire"},
    "dragon_attack": {"title": "The Dragon's Flame",
                      "desc": "a farmer charging a vast green dragon with a "
                              "small knife as fire gathers in the dragon's throat",
                      "chars": ["farmer", "dragon"],
                      "mood": "doomed charge, fire kindling"},
    "dragon_sneak": {"title": "Sneaking Past",
                     "desc": "a farmer pressing into the shadows to slip past "
                             "a vast green dragon whose tail sweeps the stone",
                     "chars": ["farmer", "dragon"],
                     "mood": "tense stealth, watching eye"},
    "dragon_caught": {"title": "The Dragon's Flame",
                      "desc": "a vast green dragon pinning a farmer to the "
                              "stone with its tail, fire kindling in its throat",
                      "chars": ["farmer", "dragon"],
                      "mood": "trapped, fire imminent"},
    "dragon_free": {"title": "Past the Dragon",
                    "desc": "a vast green dragon shifting aside to let a "
                            "farmer pass, a dark castle wall rising ahead",
                    "chars": ["farmer", "dragon"],
                    "mood": "reluctant respect, castle ahead"},
    "wood": {"title": "The Dark Wood",
             "desc": "a dark close wood with crowded trees, pale drifting "
                     "lights bobbing between the trunks off the path",
             "chars": ["farmer"], "mood": "dark, eerie, no birds"},
    "wood_light": {"title": "The Wisps",
                   "desc": "pale lovely will-o'-the-wisps dancing over a dark "
                           "marsh ahead of a farmer, the ground soft and wet",
                   "chars": ["farmer"], "mood": "eerie beauty, marsh glow"},
    "wood_swamp": {"title": "The Bog",
                   "desc": "a farmer sinking into a dark bog, marsh closing "
                           "over his chest, pale lights dancing beyond reach",
                   "chars": ["farmer"], "mood": "drowning marsh, cold"},
    "wood_river": {"title": "The River",
                   "desc": "a black fast loud river with a fallen tree "
                           "spanning it like a bridge, white water churning "
                           "around rocks",
                   "chars": ["farmer"], "mood": "dark rushing water"},
    "river_wade": {"title": "The Current",
                   "desc": "a farmer being swept under by a cold black river, "
                           "the current closing over his head",
                   "chars": ["farmer"], "mood": "cold, swallowed by water"},
    "wood_cross": {"title": "The Far Bank",
                   "desc": "a farmer crossing a fallen tree over a roaring "
                           "river, dropping onto the far bank",
                   "chars": ["farmer"], "mood": "careful crossing"},
    "wood_wolf": {"title": "The Wolves",
                  "desc": "wolves stepping out of the dark to ring a farmer "
                          "in a slow circle, eyes like coals, hackles raised",
                  "chars": ["farmer"], "mood": "encircled, menacing"},
    "wolf_attack": {"title": "The Wolves",
                    "desc": "a wolf pack closing on a running farmer in a "
                            "dark wood",
                    "chars": ["farmer"], "mood": "panic, dark swallow"},
    "wood_edge": {"title": "Out of the Wood",
                  "desc": "a farmer holding his ground against retreating "
                          "wolves, a black castle wall rising ahead",
                  "chars": ["farmer"], "mood": "standoff, dawn breaking"},
    "gate": {"title": "The Castle Gate",
             "desc": "a massive castle gate with torches burning in iron "
                     "brackets, guards beneath the arch, a black tower "
                     "looming above",
             "chars": ["farmer"], "mood": "imposing, torchlit"},
    "gate_guards": {"title": "The Guards",
                    "desc": "broad guards in dark steel at a castle gate, "
                            "their captain stepping forward with one hand on "
                            "his sword, facing a farmer",
                    "chars": ["farmer", "captain"],
                    "mood": "confrontation, torchlight"},
    "gate_talk": {"title": "The Guard Captain",
                  "desc": "a scarred guard captain in dark steel listening to "
                          "a farmer at a castle gate, a flicker of shared "
                          "grief in his face",
                  "chars": ["farmer", "captain"],
                  "mood": "tense sympathy, torchlight"},
    "gate_fight": {"title": "The Guards' Swords",
                   "desc": "guards in dark steel closing on a farmer at a "
                           "castle gate, swords drawn",
                   "chars": ["farmer", "captain"],
                   "mood": "overwhelmed, cold steel"},
    "gate_wall": {"title": "The Wall",
                  "desc": "a farmer following a castle wall as torchlight "
                          "fades, a dark drain low in the stone where moat "
                          "water runs out",
                  "chars": ["farmer"], "mood": "stealth, fading light"},
    "wall_climb": {"title": "Scaling the Wall",
                   "desc": "a farmer digging his fingers into the cracks of "
                           "a castle wall, climbing, a stone coming loose "
                           "under his foot",
                   "chars": ["farmer"], "mood": "climbing, danger, night"},
    "wall_fall": {"title": "The Wall",
                  "desc": "a farmer falling from a castle wall, the wall "
                          "rushing past, stones below",
                  "chars": ["farmer"], "mood": "plunging, night"},
    "wall_drain": {"title": "The Drain",
                   "desc": "a farmer crawling through a dark stone drain, "
                           "cold water to his chest, a grate of light ahead",
                   "chars": ["farmer"], "mood": "cramped, wet, cold"},
    "courtyard": {"title": "The Courtyard",
                  "desc": "a wide open castle courtyard swept by torchlight, "
                          "guards pacing the walls, a kitchen door ajar",
                  "chars": ["farmer"], "mood": "open, exposed, torchlight"},
    "courtyard_open": {"title": "Seen in the Yard",
                       "desc": "a farmer stepping into the open courtyard as "
                               "a shout goes up, guards turning toward him",
                       "chars": ["farmer"], "mood": "alarm, torchlight"},
    "courtyard_death": {"title": "The Chase",
                        "desc": "a farmer running across a courtyard with no "
                                "opening doors, guards closing in with swords",
                        "chars": ["farmer"], "mood": "hunted, closing in"},
    "dungeon": {"title": "The Dungeon",
                "desc": "a farmer thrown into a dark cold cell, an iron door "
                        "clanging shut, wet straw on the floor",
                "chars": ["farmer"], "mood": "bleak, cold dark"},
    "dungeon_wizard": {"title": "The Prisoner",
                       "desc": "an old wizard in torn grey robes reaching "
                               "through the bars of a dungeon cell to press a "
                               "smooth black stone into a farmer's hand",
                       "chars": ["farmer", "wizard"],
                       "mood": "dim hope, torchlight"},
    "dungeon_despair": {"title": "The Long Dark",
                        "desc": "a farmer slumped alone in a dark dungeon "
                                "cell, the fight gone out of him",
                        "chars": ["farmer"], "mood": "hopeless, cold dark"},
    "kitchen": {"title": "The Kitchen",
                "desc": "a blaze of fire and clatter in a castle kitchen, a "
                        "kind serving girl passing with a tray of bread, a "
                        "farmer slipping through",
                "chars": ["farmer", "servant"],
                "mood": "warm chaos, firelight"},
    "passage": {"title": "The Servants' Passage",
                "desc": "a narrow dark servants' passage running behind "
                        "castle walls, a farmer moving through it",
                "chars": ["farmer"], "mood": "secretive, dark"},
    "great_hall": {"title": "The Great Hall",
                   "desc": "a vast cold great hall full of courtiers in black, "
                           "a king on an iron throne at the far end, a narrow "
                           "stair winding up behind him",
                   "chars": ["farmer", "king"],
                   "mood": "imposing grandeur, cold"},
    "throne_approach": {"title": "Toward the Throne",
                        "desc": "a farmer stepping out from the shadows as a "
                                "court parts around him, the king's eyes "
                                "finding him from an iron throne",
                        "chars": ["farmer", "king"],
                        "mood": "spotlight, scrutiny"},
    "throne_seen": {"title": "Before the Throne",
                    "desc": "a cold-eyed king looking down at a farmer from "
                            "his iron throne, amused, guards watching",
                    "chars": ["farmer", "king"],
                    "mood": "cruel amusement"},
    "throne_demand": {"title": "The Demand",
                      "desc": "a farmer stepping forward in a silent great "
                              "hall to demand his wife, the king's smile "
                              "fading as guards draw swords",
                      "chars": ["farmer", "king"],
                      "mood": "defiance, tension"},
    "spire_stairs": {"title": "The Spire Stairs",
                     "desc": "a narrow winding stair climbing a dark tower, "
                             "worn smooth, air thin and cold, shadow far below",
                     "chars": ["farmer"], "mood": "ascending dread"},
    "spire": {"title": "The Black Spire",
              "desc": "a round high room lit by a fire with no wood, burning "
                      "at the heart of a great iron device, a farmer's wife "
                      "standing behind a shimmering veil",
              "chars": ["farmer", "wife"],
              "mood": "otherworldly, humming light"},
    "queen_ghost": {"title": "The Queen's Ghost",
                    "desc": "a pale translucent woman in a white gown "
                            "standing in the shadows of a dark tower room, "
                            "warning a farmer",
                    "chars": ["farmer", "queen_ghost"],
                    "mood": "ghostly, soft glow"},
    "spire_trap": {"title": "The Spell",
                   "desc": "a farmer reaching for a humming iron device as "
                           "the spell inside wakes like a snake of light",
                   "chars": ["farmer"], "mood": "magical danger, searing"},
    "wife_found": {"title": "Your Wife",
                   "desc": "a farmer and his wife embracing behind a "
                           "shimmering veil in a dark tower room, she pale "
                           "and thin but alive",
                   "chars": ["farmer", "wife"],
                   "mood": "relief, tender"},
    "king_face": {"title": "The King",
                  "desc": "a cold-eyed king standing in the doorway of a "
                          "tower room, dragon-fire flaring at his command, a "
                          "farmer and his wife standing together",
                  "chars": ["farmer", "king", "wife"],
                  "mood": "confrontation, fire flares"},
    "king_fight": {"title": "The Fight",
                   "desc": "a farmer lunging at a cold-eyed king as fire "
                           "leaps to guard him, the room turning to heat and "
                           "shadow, a fallen torch burning",
                   "chars": ["farmer", "king"],
                   "mood": "violent, heat and shadow"},
    "spell_break": {"title": "The Unmaking",
                    "desc": "a farmer throwing himself at the heart of a "
                            "great iron device, dragon-fire roaring around him",
                    "chars": ["farmer"], "mood": "apocalyptic blaze"},
    "escape_run": {"title": "The Long Stair",
                   "desc": "a farmer and his wife running hand in hand down a "
                           "winding tower stair, fire licking at their heels",
                   "chars": ["farmer", "wife"],
                   "mood": "desperate flight"},
    "dragon_ally": {"title": "The Dragon's Chains",
                    "desc": "a farmer calling out to a vast dragon chained "
                            "deep beneath a tower, the ancient beast lifting "
                            "its head",
                    "chars": ["farmer", "dragon"],
                    "mood": "awakening, chains"},
    "good_punish": {"title": "The King Falls",
                    "desc": "a farmer driving a fallen torch at a cold-eyed "
                            "king, the golden crown clattering away, dawn "
                            "light breaking, his wife watching",
                    "chars": ["farmer", "king", "wife"],
                    "mood": "victory, dawn"},
    "good_break_spell": {"title": "The Unmade Spell",
                         "desc": "a farmer quenching a dragon-fire at the "
                                 "heart of a dying iron device as the veil "
                                 "falls, an old wizard looking on and a "
                                 "dragon flying away",
                         "chars": ["farmer", "wife", "wizard", "dragon"],
                         "mood": "liberation, light returns"},
    "good_escape": {"title": "The Long Road Home",
                    "desc": "a farmer and his wife running far from a distant "
                            "black tower, reaching their farmhouse with a "
                            "fire lit and the door barred",
                    "chars": ["farmer", "wife"],
                    "mood": "safe haven, warm night"},
    "good_dragon": {"title": "The Dragon Freed",
                    "desc": "a vast dragon rising from beneath a collapsing "
                            "black tower, shaking off its chains, circling in "
                            "the morning sky as a farmer and his wife watch",
                    "chars": ["farmer", "wife", "dragon"],
                    "mood": "triumph, morning light"},
    "wife_slain": {"title": "She Is Gone",
                   "desc": "a farmer holding his fallen wife as a tower room "
                           "burns down around them, the cold-eyed king "
                           "standing over them",
                   "chars": ["farmer", "wife", "king"],
                   "mood": "grief, fire consuming"},
    "both_slain": {"title": "Together",
                   "desc": "a farmer and a cold-eyed king falling together "
                           "into a blaze, his wife's hand reaching for him",
                   "chars": ["farmer", "king", "wife"],
                   "mood": "tragic inferno"},
    "farmer_slain": {"title": "The Door",
                     "desc": "a farmer shoving a heavy door closed, fire "
                             "coming through the wood and stone and smoke",
                     "chars": ["farmer"], "mood": "sacrifice, fire and smoke"},
}

# ----------------------------------------------------------------------------
# Prompt builder
# ----------------------------------------------------------------------------
def build_prompt(sid):
    s = SCENES[sid]
    chars = " ".join(CHARACTERS[c] for c in s["chars"]) or "No characters."
    return (
        "%s\n\n"
        "Scene: %s - %s.\n\n"
        "Characters: %s\n\n"
        "Mood and lighting: %s. No text, no words, no watermark, no caption."
    ) % (STYLE, s["title"], s["desc"], chars, s["mood"])


API_URL = "https://api.openai.com/v1/images/generations"


def _get_key():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    # fall back to the Hermes env file (this worker does not inherit it)
    env_path = os.path.expanduser("/root/.hermes/.env")
    try:
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def _generate(key, prompt, timeout=300):
    """One API call -> (http_status, png_bytes, created). Raises HTTPError."""
    body = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": "1024x1024",
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": "Bearer %s" % key,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    b64 = data["data"][0]["b64_json"]
    png = base64.b64decode(b64)
    return r.status, png, data.get("created")


def _gen_one(sid, key, out_dir, orig_dir, retries=7):
    from PIL import Image  # noqa: E402  (lazy so --check needs no Pillow)
    """Generate one scene image; return a metadata dict. Never raises."""
    prompt = build_prompt(sid)
    last = None
    for attempt in range(retries):
        try:
            status, png, created = _generate(key, prompt)
            if not png or png[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError("non-PNG payload")
            # genuine 1024x1024 original
            im = Image.open(io.BytesIO(png)).convert("RGB")
            assert im.size == (1024, 1024), im.size
            orig_path = os.path.join(orig_dir, sid + ".png")
            open(orig_path, "wb").write(png)
            # 512x512 engine copy
            small = im.resize((512, 512), Image.LANCZOS)
            out_path = os.path.join(out_dir, sid + ".png")
            small.save(out_path, "PNG")
            return {
                "scene": sid,
                "ok": True,
                "http": status,
                "created": created,
                "prompt": prompt,
                "orig_bytes": len(png),
                "engine_bytes": os.path.getsize(out_path),
                "dims": "1024x1024 -> 512x512",
            }
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, ValueError, OSError, AssertionError) as e:
            last = "%s: %s" % (type(e).__name__,
                               getattr(e, "code", "") or str(e)[:120])
            wait = min(30, 2 ** attempt)
            time.sleep(wait)
    return {"scene": sid, "ok": False, "error": last, "prompt": prompt}


def _write_character_sheet(path):
    lines = [
        "# Black Spire - Art Style & Character Sheet",
        "",
        "Locked art style (fixed by Rick, used for every illustration):",
        "",
        "> %s" % STYLE,
        "",
        "Every illustration is generated with the OpenAI Images API "
        "(gpt-image-1, 1024x1024).  Each recurring character has ONE fixed "
        "written description below; that exact text is injected verbatim into "
        "every scene prompt the character appears in, so the same person "
        "renders identically across the whole set.",
        "",
    ]
    names = {
        "farmer": "The Farmer (you)", "wife": "Lena (the farmer's wife)",
        "king": "King Aldric", "wizard": "The Wizard",
        "dragon": "The Dragon", "herald": "The Old Woman",
        "neighbor": "The Neighbor", "captain": "The Guard Captain",
        "servant": "The Serving Girl", "queen_ghost": "The Queen's Ghost",
    }
    for key, description in CHARACTERS.items():
        lines.append("## %s" % names[key])
        lines.append("")
        lines.append(description)
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_manifest(manifest_path):
    import sys as _sys
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _sys.path.insert(0, here)
    from black_spire import story  # noqa: E402
    data = {
        "format": "blackspire-image-manifest",
        "version": 2,
        "note": (
            "Per-scene illustration manifest, keyed by scene id -> image "
            "filename under assets/images/.  Node 3 landed the real AI art "
            "set: one gpt-image-1 illustration per scene id, with the 1024x1024 "
            "originals under assets/images/originals/."
        ),
        "default": "farm.png",
        "scenes": {sid: "%s.png" % sid for sid in story.SCENES},
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate the Black Spire art set")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None,
                    help="only generate the first N scenes (for testing)")
    ap.add_argument("--only", type=str, default=None,
                    help="comma-separated scene ids to generate")
    ap.add_argument("--check", action="store_true",
                    help="verify the on-disk art set and exit")
    args = ap.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "assets", "images")
    orig_dir = os.path.join(out_dir, "originals")
    manifest_path = os.path.join(out_dir, "manifest.json")
    os.makedirs(orig_dir, exist_ok=True)
    os.makedirs(os.path.join(root, "docs"), exist_ok=True)

    if args.check:
        return _check(root, out_dir, orig_dir, manifest_path)

    key = _get_key()
    if not key:
        print("OPENAI_API_KEY not found", file=sys.stderr)
        return 2

    # always (re)write the character sheet and manifest from the data above
    _write_character_sheet(os.path.join(root, "docs", "character_sheet.md"))
    _write_manifest(manifest_path)

    ids = list(SCENES.keys())
    if args.only:
        ids = [s for s in args.only.split(",") if s in SCENES]
    if args.limit:
        ids = ids[: args.limit]

    print("generating %d scenes with %d workers" % (len(ids), args.workers))
    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_gen_one, sid, key, out_dir, orig_dir): sid
                for sid in ids}
        for fut in as_completed(futs):
            r = fut.result()
            results[r["scene"]] = r
            print("[%s] %s" % (r["scene"],
                               "ok %s bytes %s" % (r.get("http"), r.get("orig_bytes"))
                               if r["ok"] else "FAIL %s" % r.get("error")),
                  flush=True)

    ok = [r for r in results.values() if r["ok"]]
    bad = [r for r in results.values() if not r["ok"]]
    # record prompts (only the scenes we actually generated)
    prompts_path = os.path.join(root, "docs", "image_prompts.json")
    try:
        with open(prompts_path, "r", encoding="utf-8") as f:
            prompts = json.load(f)
    except (OSError, ValueError):
        prompts = {}
    prompts.setdefault("style", STYLE)
    prompts.setdefault("model", "gpt-image-1")
    prompts.setdefault("size", "1024x1024")
    prompts.setdefault("scenes", {})
    for r in ok:
        prompts["scenes"][r["scene"]] = {
            "prompt": r["prompt"], "http": r["http"],
            "created": r.get("created"),
            "orig_bytes": r["orig_bytes"],
            "engine_bytes": r["engine_bytes"],
            "dims": r["dims"],
        }
    with open(prompts_path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2)
        f.write("\n")

    print("ok=%d fail=%d" % (len(ok), len(bad)))
    if bad:
        print("FAILED scenes: %s" % ", ".join(sorted(r["scene"] for r in bad)))
    return 0 if not bad else 1


def _check(root, out_dir, orig_dir, manifest_path):
    import sys as _sys
    _sys.path.insert(0, root)
    from black_spire import story  # noqa: E402
    problems = []
    ids = list(story.SCENES)
    for sid in ids:
        p = os.path.join(out_dir, sid + ".png")
        o = os.path.join(orig_dir, sid + ".png")
        if not os.path.exists(p):
            problems.append("%s: missing 512 engine PNG" % sid)
        if not os.path.exists(o):
            problems.append("%s: missing 1024 original PNG" % sid)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)["scenes"]
    for sid in ids:
        if manifest.get(sid) != "%s.png" % sid:
            problems.append("%s: manifest mismatch" % sid)
    if set(manifest) != set(ids):
        problems.append("manifest scene set mismatch")
    # placeholder fallback files must be gone
    for leftover in ("death.png", "castle.png"):
        if os.path.exists(os.path.join(out_dir, leftover)):
            problems.append("placeholder fallback still present: %s" % leftover)
    if problems:
        print("\n".join("  - " + p for p in problems))
        return 1
    print("art set OK: %d scenes, originals + engine copies present, "
          "manifest in sync" % len(ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
