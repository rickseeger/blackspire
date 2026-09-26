"""Character sheet for Black Spire.

Each recurring character has ONE fixed written description.  That text is the
single source of truth for the character's appearance: it is injected verbatim
into every scene prompt the character appears in (see tools/generate_artset.py),
it is committed to docs/character_sheet.md, and it is mirrored here so game and
tool code can reason about the cast.  ``black_spire.consistency`` verifies all
three copies stay byte-for-byte identical, so the same person renders
identically in every scene.

Each entry also keeps a color palette, used only by the legacy placeholder art
generator (tools/generate_assets.py); the final node-3 art is OpenAI-generated
and does not use it.

Cast (fixed, consistent across every scene they appear in):
    farmer        - the player, a poor farmer
    wife          - Lena, the farmer's wife, taken by the king
    king          - King Aldric, the widower king
    wizard        - the hermit who opposes the king and knows the Spire's secret
    dragon        - the ancient drake bound beneath the Spire; the king borrows its fire
    herald        - the old village woman who warns the farmer
    neighbor      - the villager who tells the farmer what happened
    captain       - the king's guard captain, an honest soldier who does not love his orders
    servant       - a kind kitchen serving girl
    queen_ghost   - the dead queen, taken the same way years ago, who lingers in the Spire
"""

CHARACTERS = {
    "farmer": {
        "name": "The Farmer (you)",
        "role": "player",
        "description": (
            "The Farmer: a wiry man in his forties with sun-browned skin, short "
            "dark brown hair, a weathered kind face and tired eyes, wearing a "
            "patched brown linen tunic, grey-brown trousers and worn leather "
            "boots, with calloused hands."
        ),
        "palette": {
            "tunic": (120, 81, 45),       # patched brown tunic
            "skin": (196, 154, 108),      # sun-browned
            "hair": (61, 43, 31),         # dark brown
            "trousers": (70, 70, 75),
        },
    },
    "wife": {
        "name": "Lena (the farmer's wife)",
        "role": "the most beautiful woman in the village, taken by the king",
        "description": (
            "Lena the farmer's wife: a gentle, beautiful woman with long dark "
            "brown hair in a single braid, warm eyes and soft features, wearing "
            "a faded blue dress and a white apron dusted with flour."
        ),
        "palette": {
            "dress": (92, 122, 172),      # faded blue
            "hair": (42, 32, 52),         # dark braided
            "skin": (212, 178, 138),
        },
    },
    "king": {
        "name": "King Aldric",
        "role": "the widower king who takes the farmer's wife",
        "description": (
            "King Aldric: a tall, gaunt king with pale skin, sharp cold features, "
            "slicked-back black hair and cold grey eyes, wearing long black robes "
            "trimmed in crimson beneath a thin golden crown."
        ),
        "palette": {
            "robe": (44, 26, 34),         # black
            "crimson": (152, 32, 40),     # crimson trim
            "crown": (214, 182, 66),      # thin gold
            "skin": (224, 196, 166),
        },
    },
    "wizard": {
        "name": "The Wizard",
        "role": "a hermit who opposes the king and knows the Spire's secret",
        "description": (
            "The Wizard: a hunched old wizard with a long white beard, deep-set "
            "grey eyes and a weathered wrinkled face, wearing grey robes, leaning "
            "on a gnarled wooden staff."
        ),
        "palette": {
            "robe": (122, 124, 134),      # gray
            "beard": (230, 232, 234),     # white
            "staff": (96, 62, 40),
            "skin": (214, 190, 162),
        },
    },
    "dragon": {
        "name": "The Dragon",
        "role": "an ancient drake bound beneath the Spire; the king borrows its fire",
        "description": (
            "The Dragon: a vast ancient dragon with emerald-green scales and a "
            "pale underbelly, huge leathery wings and golden knowing eyes, with "
            "smoke curling from its nostrils."
        ),
        "palette": {
            "scales": (60, 108, 70),      # green
            "belly": (150, 168, 120),
            "eye": (222, 178, 60),        # old gold
            "smoke": (96, 96, 104),
        },
    },
    "herald": {
        "name": "The Old Woman",
        "role": "a village herald who warns the farmer the queen is dead",
        "description": (
            "The Old Woman: a bent, frail old woman with white hair and a "
            "weathered wrinkled face, wearing a grey shawl over a dark dress, "
            "leaning on a wooden walking stick."
        ),
        "palette": {
            "shawl": (122, 122, 130),     # gray
            "dress": (80, 76, 84),
            "hair": (200, 200, 200),
            "skin": (206, 172, 140),
        },
    },
    "neighbor": {
        "name": "The Neighbor",
        "role": "a villager who tells the farmer what happened",
        "description": (
            "The Neighbor: a sturdy middle-aged villager with a worried face and "
            "a brown beard, wearing a brown wool coat over a plain linen shirt."
        ),
        "palette": {
            "coat": (104, 92, 70),        # wool brown
            "shirt": (196, 190, 178),
            "skin": (206, 172, 140),
        },
    },
    "captain": {
        "name": "The Guard Captain",
        "role": "the king's captain of the guard, an honest soldier who does not love his orders",
        "description": (
            "The Guard Captain: a broad, scarred soldier with a shaved head and "
            "a short beard, grim expression, wearing dark steel armor and a "
            "black cloak."
        ),
        "palette": {
            "steel": (96, 100, 112),      # dark steel
            "cloak": (44, 30, 36),
            "skin": (210, 176, 148),
        },
    },
    "servant": {
        "name": "The Serving Girl",
        "role": "a kind kitchen servant who helps the farmer slip through the castle",
        "description": (
            "The Serving Girl: a quick, kind young serving girl with brown hair "
            "tied back, wearing a linen apron over a simple brown dress, carrying "
            "a tray of bread."
        ),
        "palette": {
            "apron": (214, 210, 196),
            "dress": (120, 84, 60),
            "hair": (90, 60, 40),
        },
    },
    "queen_ghost": {
        "name": "The Queen's Ghost",
        "role": "the dead queen, taken the same way years ago, who lingers in the Spire",
        "description": (
            "The Queen's Ghost: a pale, translucent woman with long dark hair and "
            "sad eyes, wearing a flowing white gown, faint and ethereal with a "
            "soft glow."
        ),
        "palette": {
            "gown": (222, 224, 230),      # pale white
            "glow": (200, 210, 230),
            "skin": (208, 212, 220),
        },
    },
}
