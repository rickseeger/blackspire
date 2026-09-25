"""Character sheet for Black Spire.

Each recurring character has a one-line written description (fixed identity the
story and the art must both respect) and a color palette used to draw them in
the placeholder art.  The art generator (tools/generate_assets.py) reads the
farmer's palette so the picture matches the written description; the remaining
palettes are carried forward for the art node (node 3) to build full sheets
from.

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
            "A wiry, sun-browned man in a patched brown tunic, with calloused "
            "hands and tired, kind eyes."
        ),
        "palette": {
            "tunic": (120, 81, 45),       # patched brown tunic
            "skin": (196, 154, 108),      # sun-browned
            "hair": (61, 43, 31),         # dark brown
            "trousers": (70, 70, 75),
        },
    },
    "wife": {
        "name": "Lena, the Farmer's Wife",
        "role": "the most beautiful woman in the village, taken by the king",
        "description": (
            "A gentle woman with dark braided hair and a faded blue dress, "
            "flour dusted on her hands."
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
            "A tall, cold-eyed king in black and crimson robes beneath a thin "
            "golden crown."
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
            "A hunched old wizard in gray robes with a gnarled staff and a "
            "long white beard."
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
            "A vast, green-scaled dragon with smoke curling from its nostrils "
            "and old, knowing eyes."
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
            "A bent old woman in a gray shawl, with a grip strong for her "
            "years and a crow's warning on her tongue."
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
            "A sturdy, worried villager in a wool coat who meets the farmer "
            "at his open door."
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
            "A broad, scarred soldier in dark steel who carries the same grief "
            "he is ordered to enforce."
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
            "A quick, kind serving girl in an apron, carrying a tray of bread "
            "and pretending not to see the farmer."
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
            "A pale, translucent woman in a white gown, sad-eyed, who warns "
            "the farmer of the stolen fire."
        ),
        "palette": {
            "gown": (222, 224, 230),      # pale white
            "glow": (200, 210, 230),
            "skin": (208, 212, 220),
        },
    },
}
