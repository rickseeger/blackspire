"""Character sheet for Black Spire.

Each recurring character has a one-line written description and the exact
color palette used to draw them in the placeholder art.  The art generator
(tools/generate_assets.py) reads from this same sheet, so the picture and the
written description can never drift apart.  Node 3 replaces the placeholder
art but keeps these identities.
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
        "name": "The Farmer's Wife",
        "role": "the most beautiful woman in the village",
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
        "name": "The King",
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
        "role": "a hermit of the Black Spire foothills",
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
}
