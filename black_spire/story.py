"""The Black Spire story graph (proof-of-concept slice).

This is a cheap vertical slice, not the full 60-scene game.  The graph is
data-driven: each scene has an id, a title, an ambient bed, an illustration,
plain prose, and a list of choices.  A choice may carry a one-shot action
sound that plays when it is selected (the "choice-triggered action sound").
The death scene is flagged separately so the engine knows when to toll the
single large death bell.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Choice:
    label: str
    target: str
    action_sound: Optional[str] = None


@dataclass(frozen=True)
class Scene:
    id: str
    title: str
    ambient: str          # ambient loop id ("none" for silence)
    image: str            # illustration asset stem
    text: str             # body prose
    choices: Tuple[Choice, ...]


SCENES = {
    "farm": Scene(
        id="farm",
        title="The Farm",
        ambient="farm",
        image="farm",
        text=(
            "The sun comes up over your farm. Chickens scratch in the dirt. "
            "Sheep bleat out in the field. Inside the house, your wife hums "
            "as she kneads bread.\n\n"
            "You are a poor farmer. Today you have an errand in the village."
        ),
        choices=(
            Choice("Run the errand to the village", "errand"),
            Choice("Feed the animals first", "animals"),
        ),
    ),
    "animals": Scene(
        id="animals",
        title="The Animals",
        ambient="farm",
        image="farm",
        text=(
            "You scatter grain for the chickens and check the sheep. It calms "
            "you. But the sun climbs, and the errand will not wait."
        ),
        choices=(
            Choice("Set off for the village", "errand"),
        ),
    ),
    "errand": Scene(
        id="errand",
        title="The Errand",
        ambient="road",
        image="errand",
        text=(
            "You walk the dusty road to the village. You sell your eggs and "
            "buy salt. As you turn for home, an old woman seizes your arm.\n\n"
            "\"Hurry home, farmer,\" she says. \"The queen is dead.\""
        ),
        choices=(
            Choice("Run home at once", "return", action_sound="run"),
            Choice("Ask the old woman what happened", "return"),
        ),
    ),
    "return": Scene(
        id="return",
        title="Home",
        ambient="farm",
        image="return",
        text=(
            "You run home. The door hangs open. Your wife is gone.\n\n"
            "A neighbor tells you the truth. The queen is dead. The king "
            "needs a new queen. He has taken the most beautiful woman in the "
            "village \u2014 your wife. He has carried her to the castle, to the "
            "Black Spire."
        ),
        choices=(
            Choice("Set out for the castle", "road", action_sound="gallop"),
            Choice("Gather a few things first", "road"),
        ),
    ),
    "road": Scene(
        id="road",
        title="The Fork in the Road",
        ambient="road",
        image="road",
        text=(
            "You set out. The Black Spire is a dark finger against the sky. "
            "The road forks ahead.\n\n"
            "One path climbs the mountain. The other sinks into a dark wood."
        ),
        choices=(
            Choice("Take the high mountain path", "death", action_sound="scream"),
            Choice("Take the low road through the wood", "castle_gate"),
        ),
    ),
    "death": Scene(
        id="death",
        title="The Fall",
        ambient="none",
        image="death",
        text=(
            "The path crumbles beneath you. You fall into the dark. The world "
            "spins. Then there is nothing at all."
        ),
        choices=(
            Choice("Try again", "farm"),
        ),
    ),
    "castle_gate": Scene(
        id="castle_gate",
        title="The Castle Gate",
        ambient="road",
        image="castle",
        text=(
            "You come to the castle gate. Torches burn. The Spire looms above. "
            "You have no sword and no army \u2014 but you are not turning back.\n\n"
            "(End of the slice \u2014 to be continued.)"
        ),
        choices=(),
    ),
}

START_SCENE = "farm"
DEATH_SCENE = "death"
DEATH_BELL = "bell"


def validate_graph():
    """Return a list of problems; an empty list means the graph is sound."""
    problems = []
    if START_SCENE not in SCENES:
        problems.append("start scene %r missing" % START_SCENE)
    for sid, scene in SCENES.items():
        for i, choice in enumerate(scene.choices):
            if choice.target not in SCENES:
                problems.append(
                    "%s.choices[%d] (%r) -> %r missing" % (sid, i, choice.label, choice.target)
                )
    return problems


class StoryEngine:
    """Pure story navigation (no pygame) \u2014 easy to drive from tests."""

    def __init__(self, scenes=None, start=None):
        self.scenes = scenes if scenes is not None else SCENES
        self.start = start if start is not None else START_SCENE
        self.current = self.start

    def scene(self):
        return self.scenes[self.current]

    def choices(self):
        return self.scene().choices

    def choose(self, index):
        """Apply the choice at ``index`` and return the new scene id."""
        self.current = self.choices()[index].target
        return self.current
