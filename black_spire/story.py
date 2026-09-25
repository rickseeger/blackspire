"""The Black Spire story graph (complete ~68-scene game).

Data-driven, same schema as the node-1 proof-of-concept slice, extended with a
per-scene ``kind`` (``"scene"`` / ``"death"`` / ``"good"``) so the engine can
distinguish terminal endings from ordinary beats.  A death scene ends the run
with the single death bell and a "Try again" choice back to the start; a good
ending ends the run with a "Play again" choice back to the start.

Fixed cast (one-line descriptions in ``characters.py``):
    farmer, wife (Lena), the king, the wizard, the dragon, the herald,
    the neighbor, the guard captain, the servant, the queen's ghost.

Every choice resolves to a valid next scene id; there are no dangling edges.
The graph is continuous and cohesive down every path: mountain and wood routes
rejoin at the castle gate, both lead to the Black Spire, and from the Spire
every death and every good ending is reachable.
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
    ambient: str          # ambient loop id (one of audio.AMBIENTS)
    image: str            # illustration asset stem
    text: str             # body prose
    choices: Tuple[Choice, ...] = ()
    kind: str = "scene"   # "scene" | "death" | "good"


SCENES = {
    # ---------------------------------------------------------------- opening
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
            Choice("Run the errand to the village", "errand", action_sound="steps"),
            Choice("Feed the animals first", "animals", action_sound="steps"),
        ),
    ),
    "animals": Scene(
        id="animals",
        title="The Animals",
        ambient="farm",
        image="farm",
        text=(
            "You scatter grain for the chickens and check the sheep. The "
            "animals are calm, and it steadies you. But the sun climbs, and "
            "the errand will not wait."
        ),
        choices=(
            Choice("Set off for the village", "errand", action_sound="steps"),
            Choice("Go inside to kiss your wife goodbye", "farewell", action_sound="door"),
        ),
    ),
    "farewell": Scene(
        id="farewell",
        title="Farewell",
        ambient="farm",
        image="farm",
        text=(
            "You step inside to kiss your wife goodbye. She smiles and "
            "brushes flour from your sleeve.\n\n"
            "\"Come home before dark,\" she says. \"I'll keep the fire lit.\"\n\n"
            "You promise her you will."
        ),
        choices=(
            Choice("Set off for the village", "errand", action_sound="steps"),
            Choice("Walk her to the gate and kiss her one more time", "errand", action_sound="steps"),
        ),
    ),
    "errand": Scene(
        id="errand",
        title="The Errand",
        ambient="village",
        image="errand",
        text=(
            "You walk the dusty road to the village. You sell your eggs and "
            "buy salt. As you turn for home, an old woman seizes your arm.\n\n"
            "\"Hurry home, farmer,\" she says. \"The queen is dead.\""
        ),
        choices=(
            Choice("Run home at once", "return", action_sound="run"),
            Choice("Ask the old woman what happened", "herald", action_sound="steps"),
        ),
    ),
    "herald": Scene(
        id="herald",
        title="The Old Woman",
        ambient="village",
        image="errand",
        text=(
            "The old woman's grip is strong for her years.\n\n"
            "\"The queen is dead,\" she says again, \"and the king will want a "
            "new one. He has eyes like a crow. The most beautiful woman in "
            "every village, he takes for his own. Run home, farmer. Run now.\"\n\n"
            "She lets go of your arm. Her warning hangs in the air."
        ),
        choices=(
            Choice("Run home", "return", action_sound="run"),
            Choice("Stop to thank her", "return", action_sound="steps"),
        ),
    ),
    "return": Scene(
        id="return",
        title="Home",
        ambient="farm",
        image="return",
        text=(
            "You run home. The door hangs open. Your wife is gone. The bread "
            "dough sits half-kneaded on the table.\n\n"
            "A neighbor tells you the truth. The king has taken the most "
            "beautiful woman in the village \u2014 your wife \u2014 and carried her to "
            "the castle at the Black Spire."
        ),
        choices=(
            Choice("Set out for the castle", "road", action_sound="gallop"),
            Choice("Gather a few things first", "gather", action_sound="steps"),
        ),
    ),
    "gather": Scene(
        id="gather",
        title="What You Carry",
        ambient="farm",
        image="farm",
        text=(
            "You gather what little you have: a knife, a loaf of bread, a "
            "water skin, and your father's old coat. It is not much against a "
            "king.\n\n"
            "But it will have to be enough."
        ),
        choices=(
            Choice("Set out for the castle", "road", action_sound="gallop"),
            Choice("Take one last look at home", "road", action_sound="steps"),
        ),
    ),

    # ------------------------------------------------------- the fork in the road
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
            Choice("Take the high mountain path", "mountain", action_sound="steps"),
            Choice("Take the low road through the wood", "wood", action_sound="steps"),
        ),
    ),

    # ------------------------------------------------------------ mountain route
    "mountain": Scene(
        id="mountain",
        title="The Mountain Path",
        ambient="mountain",
        image="road",
        text=(
            "The mountain path is steep and narrow, cut into the rock. Loose "
            "stones skitter down into the valley below. The wind pulls at "
            "your coat."
        ),
        choices=(
            Choice("Keep to the narrow ledge", "mountain_ledge", action_sound="steps"),
            Choice("Scramble up the loose rock", "mountain_scree", action_sound="stone"),
        ),
    ),
    "mountain_ledge": Scene(
        id="mountain_ledge",
        title="The Narrow Ledge",
        ambient="mountain",
        image="road",
        text=(
            "The path narrows to a ledge no wider than your shoulders. Far "
            "below, mist hides the valley floor. You press your back to the "
            "cold stone and edge along."
        ),
        choices=(
            Choice("Edge along carefully", "mountain_ridge", action_sound="steps"),
            Choice("Lean out for a look", "mountain_fall", action_sound="scream"),
        ),
    ),
    "mountain_scree": Scene(
        id="mountain_scree",
        title="Loose Rock",
        ambient="mountain",
        image="road",
        text=(
            "The rock under your feet is loose, a slope of broken stone that "
            "shifts with every step. One wrong move and it will carry you "
            "down with it."
        ),
        choices=(
            Choice("Dig in your heels", "mountain_ridge", action_sound="stone"),
            Choice("Leap for the far handhold", "mountain_fall", action_sound="scream"),
        ),
    ),
    "mountain_fall": Scene(
        id="mountain_fall",
        title="The Fall",
        ambient="mountain",
        image="death",
        text=(
            "The stone gives way. You fall. The wind screams past you, and "
            "the world spins, and then there is nothing at all."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "mountain_ridge": Scene(
        id="mountain_ridge",
        title="The Ridge",
        ambient="mountain",
        image="road",
        text=(
            "You reach the ridge and stop to catch your breath. Ahead, the "
            "pass climbs between two peaks. A thin thread of smoke rises from "
            "a hut nestled in the rocks. Beyond, the road drops toward the "
            "castle."
        ),
        choices=(
            Choice("Go to the wizard's hut", "wizard_hut", action_sound="steps"),
            Choice("Press on toward the pass", "dragon_pass", action_sound="steps"),
        ),
    ),
    "wizard_hut": Scene(
        id="wizard_hut",
        title="The Wizard's Hut",
        ambient="mountain",
        image="road",
        text=(
            "The hut is small and crooked, hung with herbs and bone "
            "wind-chimes. An old wizard in gray robes opens the door before "
            "you knock.\n\n"
            "\"I know why you have come,\" he says. \"The king has taken what is "
            "yours. Many have walked this road. Few have come back.\"\n\n"
            "He offers you a warm drink and a warning. \"The king's power is "
            "not his own. It is borrowed fire, a dragon bound beneath the "
            "Spire. Remember that, farmer.\""
        ),
        choices=(
            Choice("Accept his warning and advice", "dragon_pass", action_sound="magic"),
            Choice("Decline and go on alone", "dragon_pass", action_sound="steps"),
        ),
    ),
    "dragon_pass": Scene(
        id="dragon_pass",
        title="The Dragon's Pass",
        ambient="mountain",
        image="road",
        text=(
            "The pass opens into a wide ledge of scorched stone. A dragon "
            "lies across the path, vast and green-scaled, smoke curling from "
            "its nostrils.\n\n"
            "It opens one eye. It is not asleep. It is waiting."
        ),
        choices=(
            Choice("Speak to the dragon", "dragon_parley", action_sound="roar"),
            Choice("Try to slip past", "dragon_sneak", action_sound="steps"),
            Choice("Turn back toward the wood road", "wood", action_sound="steps"),
        ),
    ),
    "dragon_parley": Scene(
        id="dragon_parley",
        title="Parley with the Dragon",
        ambient="mountain",
        image="road",
        text=(
            "The dragon watches you without moving. Its voice, when it comes, "
            "is low as thunder.\n\n"
            "\"You are not the king's soldier,\" it says. \"Answer me true, and "
            "you may pass.\""
        ),
        choices=(
            Choice("Answer its riddle", "dragon_riddle", action_sound="steps"),
            Choice("Speak plainly and ask to pass", "dragon_free", action_sound="steps"),
            Choice("Attack", "dragon_attack", action_sound="sword"),
        ),
    ),
    "dragon_riddle": Scene(
        id="dragon_riddle",
        title="The Dragon's Riddle",
        ambient="mountain",
        image="road",
        text=(
            "The dragon lifts its head and asks:\n\n"
            "\"What is heavier than a mountain, yet a child can carry it?\"\n\n"
            "Its eye gleams. It is testing you."
        ),
        choices=(
            Choice("A secret", "dragon_free", action_sound="magic"),
            Choice("A stone", "dragon_wrong", action_sound="roar"),
        ),
    ),
    "dragon_wrong": Scene(
        id="dragon_wrong",
        title="The Dragon's Flame",
        ambient="mountain",
        image="death",
        text=(
            "You guess, and the dragon only sighs. \"Wrong,\" it says, and "
            "opens its mouth.\n\n"
            "Fire fills the world. There is no time to run."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "dragon_attack": Scene(
        id="dragon_attack",
        title="The Dragon's Flame",
        ambient="mountain",
        image="death",
        text=(
            "You charge the dragon with your little knife. It is almost kind "
            "about it. The fire comes all at once, and then there is nothing."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "dragon_sneak": Scene(
        id="dragon_sneak",
        title="Sneaking Past",
        ambient="mountain",
        image="road",
        text=(
            "You press yourself into the shadows and try to slip past. The "
            "dragon's tail sweeps the stone. It is watching you the whole "
            "time."
        ),
        choices=(
            Choice("Hold still and meet its eye", "dragon_parley", action_sound="steps"),
            Choice("Make a run for it", "dragon_caught", action_sound="run"),
        ),
    ),
    "dragon_caught": Scene(
        id="dragon_caught",
        title="The Dragon's Flame",
        ambient="mountain",
        image="death",
        text=(
            "The dragon's tail snaps out and pins you to the stone. It leans "
            "down, and the last thing you see is the fire kindling in its "
            "throat."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "dragon_free": Scene(
        id="dragon_free",
        title="Past the Dragon",
        ambient="mountain",
        image="road",
        text=(
            "The dragon considers you for a long moment, then shifts aside "
            "and lets you pass.\n\n"
            "\"Go,\" it rumbles. \"And remember: the king does not own the fire. "
            "He only borrows it.\"\n\n"
            "You climb down from the pass, and the castle wall rises before "
            "you."
        ),
        choices=(
            Choice("Go on toward the castle", "gate", action_sound="steps"),
            Choice("Rest a moment on the ledge", "gate", action_sound="steps"),
        ),
    ),

    # --------------------------------------------------------------- wood route
    "wood": Scene(
        id="wood",
        title="The Dark Wood",
        ambient="wood",
        image="road",
        text=(
            "The wood is dark and close. The trees crowd together, and no "
            "birds sing here. After a while you notice lights, pale and "
            "drifting, bobbing between the trunks, off the path."
        ),
        choices=(
            Choice("Keep to the path", "wood_river", action_sound="steps"),
            Choice("Follow the dancing lights", "wood_light", action_sound="magic"),
        ),
    ),
    "wood_light": Scene(
        id="wood_light",
        title="The Wisps",
        ambient="wood",
        image="road",
        text=(
            "The lights are will-o'-the-wisps, pale and lovely, dancing over "
            "the marsh. They drift just ahead of you, always just out of "
            "reach. The ground underfoot grows soft and wet."
        ),
        choices=(
            Choice("Follow the lights deeper", "wood_swamp", action_sound="magic"),
            Choice("Turn back to the path", "wood_river", action_sound="steps"),
        ),
    ),
    "wood_swamp": Scene(
        id="wood_swamp",
        title="The Bog",
        ambient="wood",
        image="death",
        text=(
            "You follow the lights too far. The marsh closes over your boots, "
            "then your knees, then your chest. The lights go on dancing. They "
            "do not help you."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "wood_river": Scene(
        id="wood_river",
        title="The River",
        ambient="wood",
        image="road",
        text=(
            "You come to a river, black and fast and loud. A fallen tree "
            "spans it like a bridge. The current below churns white around "
            "the rocks."
        ),
        choices=(
            Choice("Cross the fallen log", "wood_cross", action_sound="creak"),
            Choice("Wade across", "river_wade", action_sound="splash"),
        ),
    ),
    "river_wade": Scene(
        id="river_wade",
        title="The Current",
        ambient="wood",
        image="death",
        text=(
            "The river is deeper than it looks. The current takes your feet "
            "from under you, and the cold water closes over your head. The "
            "river keeps the rest."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "wood_cross": Scene(
        id="wood_cross",
        title="The Far Bank",
        ambient="wood",
        image="road",
        text=(
            "You cross the fallen tree, one careful step at a time, and drop "
            "onto the far bank. Behind you, the river roars. Ahead, the trees "
            "thin out."
        ),
        choices=(
            Choice("Press on into the trees", "wood_wolf", action_sound="steps"),
            Choice("Stop to wring out your boots", "wood_wolf", action_sound="steps"),
        ),
    ),
    "wood_wolf": Scene(
        id="wood_wolf",
        title="The Wolves",
        ambient="wood",
        image="road",
        text=(
            "Wolves step out of the dark. They ring you in a slow circle, "
            "eyes like coals, hackles raised. The pack has been waiting here "
            "a long time.\n\n"
            "If you run, they will have you."
        ),
        choices=(
            Choice("Stand tall and shout", "wood_edge", action_sound="wolf"),
            Choice("Throw them your bread", "wood_edge", action_sound="steps"),
            Choice("Run", "wolf_attack", action_sound="run"),
        ),
    ),
    "wolf_attack": Scene(
        id="wolf_attack",
        title="The Wolves",
        ambient="wood",
        image="death",
        text=(
            "You run, and that is the worst thing you could do. The pack is "
            "on you before you take three steps. The dark wood swallows the "
            "rest."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "wood_edge": Scene(
        id="wood_edge",
        title="Out of the Wood",
        ambient="wood",
        image="road",
        text=(
            "You do not run. You hold your ground and stare them down, and "
            "one by one the wolves lose their nerve. You back away slowly, "
            "and the pack lets you go.\n\n"
            "The castle wall rises ahead, black against the sky."
        ),
        choices=(
            Choice("Go on toward the castle", "gate", action_sound="steps"),
            Choice("Circle the wall", "gate", action_sound="steps"),
        ),
    ),

    # ----------------------------------------------------- castle gate and walls
    "gate": Scene(
        id="gate",
        title="The Castle Gate",
        ambient="castle",
        image="castle",
        text=(
            "You come to the castle gate. Torches burn in iron brackets. "
            "Guards stand beneath the arch. The Black Spire looms above them "
            "all."
        ),
        choices=(
            Choice("Walk up to the guards", "gate_guards", action_sound="steps"),
            Choice("Look for another way in", "gate_wall", action_sound="steps"),
        ),
    ),
    "gate_guards": Scene(
        id="gate_guards",
        title="The Guards",
        ambient="castle",
        image="castle",
        text=(
            "The guards are broad men in dark steel, and they do not smile. "
            "The captain steps forward, one hand on his sword.\n\n"
            "\"State your business,\" he says. \"Quickly.\""
        ),
        choices=(
            Choice("Ask to see the king", "gate_talk", action_sound="steps"),
            Choice("Rush them", "gate_fight", action_sound="sword"),
            Choice("Back away", "gate", action_sound="steps"),
        ),
    ),
    "gate_talk": Scene(
        id="gate_talk",
        title="The Guard Captain",
        ambient="castle",
        image="castle",
        text=(
            "The captain listens as you speak. When you tell him about your "
            "wife, something in his face changes, a flicker of the same grief, "
            "quickly hidden.\n\n"
            "\"I have my orders,\" he says at last. \"You should not have come "
            "here.\""
        ),
        choices=(
            Choice("Tell him the truth", "dungeon", action_sound="chains"),
            Choice("Try to talk your way past", "gate_fight", action_sound="sword"),
        ),
    ),
    "gate_fight": Scene(
        id="gate_fight",
        title="The Guards' Swords",
        ambient="castle",
        image="death",
        text=(
            "You rush the guards. There are too many, and they are too quick. "
            "The gate does not fall. You do."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "gate_wall": Scene(
        id="gate_wall",
        title="The Wall",
        ambient="castle",
        image="castle",
        text=(
            "You slip away from the gate and follow the wall until the "
            "torchlight fades. The stones are rough, and there is a dark "
            "drain low in the wall where the moat water runs out."
        ),
        choices=(
            Choice("Climb the wall", "wall_climb", action_sound="steps"),
            Choice("Find a drain", "wall_drain", action_sound="splash"),
        ),
    ),
    "wall_climb": Scene(
        id="wall_climb",
        title="Scaling the Wall",
        ambient="castle",
        image="castle",
        text=(
            "You dig your fingers into the cracks and climb. Halfway up, a "
            "stone comes loose under your foot and rattles away into the dark "
            "below."
        ),
        choices=(
            Choice("Keep climbing", "courtyard", action_sound="steps"),
            Choice("Slip", "wall_fall", action_sound="scream"),
        ),
    ),
    "wall_fall": Scene(
        id="wall_fall",
        title="The Wall",
        ambient="castle",
        image="death",
        text=(
            "Your grip fails. You fall, and the wall rushes past, and the "
            "stones at the bottom are waiting."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "wall_drain": Scene(
        id="wall_drain",
        title="The Drain",
        ambient="castle",
        image="castle",
        text=(
            "You crawl through the drain, cold water up to your chest, and "
            "come up through a grate into a dark kitchen. The air smells of "
            "bread and smoke."
        ),
        choices=(
            Choice("Crawl through", "kitchen", action_sound="splash"),
            Choice("Turn back", "gate", action_sound="steps"),
        ),
    ),
    "courtyard": Scene(
        id="courtyard",
        title="The Courtyard",
        ambient="castle",
        image="castle",
        text=(
            "The courtyard is wide and open, swept by torchlight. Guards pace "
            "the walls. Across the stones, a door stands ajar, the kitchens, "
            "by the smell of it."
        ),
        choices=(
            Choice("Cross openly", "courtyard_open", action_sound="steps"),
            Choice("Slip along the shadow", "kitchen", action_sound="steps"),
        ),
    ),
    "courtyard_open": Scene(
        id="courtyard_open",
        title="Seen in the Yard",
        ambient="castle",
        image="castle",
        text=(
            "You step out into the open, and a shout goes up. The guards have "
            "seen you. Boots pound on stone from every side."
        ),
        choices=(
            Choice("Surrender", "dungeon", action_sound="chains"),
            Choice("Run", "courtyard_death", action_sound="run"),
        ),
    ),
    "courtyard_death": Scene(
        id="courtyard_death",
        title="The Chase",
        ambient="castle",
        image="death",
        text=(
            "You run, but the courtyard has no doors that open for you. The "
            "guards close in, and their swords end the chase."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),

    # ------------------------------------------------------------------ dungeon
    "dungeon": Scene(
        id="dungeon",
        title="The Dungeon",
        ambient="castle",
        image="castle",
        text=(
            "They throw you into a cell and the iron door clangs shut. It is "
            "dark and cold, and the straw is wet.\n\n"
            "After a while, you hear breathing from the next cell. A voice, "
            "dry as old leaves: \"Well. They took someone from you too, did "
            "not they.\""
        ),
        choices=(
            Choice("Talk to the prisoner", "dungeon_wizard", action_sound="steps"),
            Choice("Work at the lock", "passage", action_sound="chains"),
            Choice("Give up hope", "dungeon_despair", action_sound="steps"),
        ),
    ),
    "dungeon_wizard": Scene(
        id="dungeon_wizard",
        title="The Prisoner",
        ambient="castle",
        image="castle",
        text=(
            "In the next cell sits an old wizard, his gray "
            "robes torn, his staff gone.\n\n"
            "\"The king throws everyone who knows the truth down here,\" he "
            "says. \"Here, take this.\" He presses a smooth black stone through "
            "the bars. \"It will open a door for you. And when you face the "
            "king, remember: the fire beneath the Spire is not his to command. "
            "He only borrows it.\""
        ),
        choices=(
            Choice("Take his charm", "passage", action_sound="magic"),
            Choice("Refuse and pick the lock yourself", "passage", action_sound="chains"),
        ),
    ),
    "dungeon_despair": Scene(
        id="dungeon_despair",
        title="The Long Dark",
        ambient="castle",
        image="death",
        text=(
            "The days run together. You stop counting them. The dark takes "
            "the fight out of you, and one morning you simply do not wake."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),

    # ------------------------------------------------------- kitchen and passage
    "kitchen": Scene(
        id="kitchen",
        title="The Kitchen",
        ambient="castle",
        image="castle",
        text=(
            "The kitchen is a blaze of fire and clatter, and no one looks "
            "twice at a farmer in a coat. A serving girl passes with a tray "
            "of bread. The servants' stair lies just beyond the larder door."
        ),
        choices=(
            Choice("Hide in the larder", "great_hall", action_sound="fire"),
            Choice("Follow the servants' stair", "passage", action_sound="creak"),
        ),
    ),
    "passage": Scene(
        id="passage",
        title="The Servants' Passage",
        ambient="castle",
        image="castle",
        text=(
            "The servants' passage is narrow and dark, running behind the "
            "walls like a vein. From somewhere ahead you hear the murmur of a "
            "crowd, and far above, the wind singing around the Spire."
        ),
        choices=(
            Choice("Climb toward the Spire", "spire_stairs", action_sound="creak"),
            Choice("Slip behind the throne", "great_hall", action_sound="steps"),
        ),
    ),

    # ------------------------------------------------------------ the great hall
    "great_hall": Scene(
        id="great_hall",
        title="The Great Hall",
        ambient="castle",
        image="castle",
        text=(
            "The great hall is vast and cold, full of courtiers in black. At "
            "its far end, on a throne of iron, sits the king. Above him, a "
            "narrow stair winds up into the Spire."
        ),
        choices=(
            Choice("Slip toward the Spire stair", "spire_stairs", action_sound="steps"),
            Choice("Step out before the king", "throne_approach", action_sound="steps"),
        ),
    ),
    "throne_approach": Scene(
        id="throne_approach",
        title="Toward the Throne",
        ambient="castle",
        image="castle",
        text=(
            "You step out from the shadows, and the court parts around you "
            "like water. The king's eyes find you. You are a farmer in a "
            "coat, and every guard in the hall is watching."
        ),
        choices=(
            Choice("Speak your demand", "throne_seen", action_sound="steps"),
            Choice("Slip away to the stair", "spire_stairs", action_sound="steps"),
        ),
    ),
    "throne_seen": Scene(
        id="throne_seen",
        title="Before the Throne",
        ambient="castle",
        image="castle",
        text=(
            "The king looks down at you from his iron throne. He is not "
            "angry. He is amused.\n\n"
            "\"A farmer,\" he says. \"Come all this way. How very brave. How "
            "very foolish.\""
        ),
        choices=(
            Choice("Demand your wife back", "throne_demand", action_sound="steps"),
            Choice("Turn and run", "courtyard_death", action_sound="run"),
        ),
    ),
    "throne_demand": Scene(
        id="throne_demand",
        title="The Demand",
        ambient="castle",
        image="castle",
        text=(
            "You step forward and demand your wife. The hall goes very still. "
            "The king's smile fades, and he raises one hand. The guards move "
            "toward you, swords sliding from their sheaths."
        ),
        choices=(
            Choice("Fight the guards", "gate_fight", action_sound="sword"),
            Choice("Let them seize you", "dungeon", action_sound="chains"),
        ),
    ),

    # ------------------------------------------------------------- the black spire
    "spire_stairs": Scene(
        id="spire_stairs",
        title="The Spire Stairs",
        ambient="spire",
        image="castle",
        text=(
            "The stair winds up and up, each step worn smooth by years of "
            "fear. The air grows thin and cold, and far below, the great hall "
            "falls away to a pit of shadow."
        ),
        choices=(
            Choice("Climb to the top", "spire", action_sound="creak"),
            Choice("Pause and look out an arrow-slit", "spire", action_sound="gasp"),
        ),
    ),
    "spire": Scene(
        id="spire",
        title="The Black Spire",
        ambient="spire",
        image="castle",
        text=(
            "The room at the top of the Spire is round and high, lit by a "
            "fire that has no wood and gives no warmth. It burns at the heart "
            "of a great iron device, the king's spell-engine, humming like a "
            "trapped storm.\n\n"
            "And there, behind a shimmering veil, stands your wife."
        ),
        choices=(
            Choice("Go to your wife", "wife_found", action_sound="steps"),
            Choice("Touch the humming device", "spire_trap", action_sound="magic"),
            Choice("Listen to the shadows", "queen_ghost", action_sound="whisper"),
        ),
    ),
    "queen_ghost": Scene(
        id="queen_ghost",
        title="The Queen's Ghost",
        ambient="spire",
        image="castle",
        text=(
            "A cold breath touches your cheek. In the shadows at the edge of "
            "the room stands a woman in a white gown, pale, translucent, "
            "sad.\n\n"
            "\"You are too late for me,\" she whispers. \"But not for her. He "
            "took me the same way, years ago. The fire in that device is not "
            "his. It is a dragon's, bound and stolen. Free it, and the king's "
            "power dies with it.\""
        ),
        choices=(
            Choice("Take her secret and go to your wife", "wife_found", action_sound="whisper"),
            Choice("Ask her how she died", "wife_found", action_sound="whisper"),
        ),
    ),
    "spire_trap": Scene(
        id="spire_trap",
        title="The Spell",
        ambient="spire",
        image="death",
        text=(
            "You reach for the humming device, and the spell inside it wakes "
            "like a snake. It coils around your heart and squeezes. The last "
            "thing you hear is your wife calling your name."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),

    # ----------------------------------------------------- the ending hub (spire)
    "wife_found": Scene(
        id="wife_found",
        title="Your Wife",
        ambient="spire",
        image="castle",
        text=(
            "The veil parts, and there she is, Lena, your wife, pale and thin "
            "but alive. She throws her arms around you and does not let go.\n\n"
            "\"I knew you would come,\" she whispers. Then, urgent: \"Listen. I "
            "have watched him. The fire at the heart of that device is what "
            "keeps his spell alive. It is a dragon's fire, stolen. Quench it "
            "or free it, and he has nothing.\"\n\n"
            "Below, boots ring on the stair. The king is coming."
        ),
        choices=(
            Choice("Step out to face the king", "king_face", action_sound="steps"),
            Choice("Grab her hand and run", "escape_run", action_sound="run"),
        ),
    ),
    "king_face": Scene(
        id="king_face",
        title="The King",
        ambient="spire",
        image="castle",
        text=(
            "The king stands in the doorway, and the dragon-fire at the heart "
            "of the device leaps and flares at his command. Your wife is at "
            "your side, her hand in yours.\n\n"
            "\"A farmer,\" the king says, \"and his stolen bride. You think you "
            "can take her from me?\""
        ),
        choices=(
            Choice("Lunge at the king", "king_fight", action_sound="sword"),
            Choice("Strike at the dragon-fire's heart", "spell_break", action_sound="fire"),
            Choice("Cry out to the dragon to be free", "dragon_ally", action_sound="roar"),
            Choice("Grab her and run", "escape_run", action_sound="run"),
        ),
    ),
    "king_fight": Scene(
        id="king_fight",
        title="The Fight",
        ambient="spire",
        image="castle",
        text=(
            "You lunge at the king. He is old and cruel, but the fire leaps "
            "to guard him, and the room turns to heat and shadow. On the "
            "stones lies a fallen torch, still burning."
        ),
        choices=(
            Choice("Seize the fallen torch and strike", "good_punish", action_sound="sword"),
            Choice("Tackle him into the flames", "both_slain", action_sound="fire"),
        ),
    ),
    "spell_break": Scene(
        id="spell_break",
        title="The Unmaking",
        ambient="spire",
        image="castle",
        text=(
            "You throw yourself at the heart of the device, the dragon-fire "
            "roaring around you. Lena's words ring in your ears: quench it, "
            "or free it. You reach into the blaze."
        ),
        choices=(
            Choice("Quench the fire for good", "good_break_spell", action_sound="magic"),
            Choice("Turn to check on your wife", "wife_slain", action_sound="sword"),
        ),
    ),
    "escape_run": Scene(
        id="escape_run",
        title="The Long Stair",
        ambient="spire",
        image="castle",
        text=(
            "You grab Lena's hand and run for the stair. The king's shout "
            "follows you, and the fire follows faster, licking at your heels "
            "down the winding steps."
        ),
        choices=(
            Choice("Run hand in hand, do not look back", "good_escape", action_sound="run"),
            Choice("Stop to bar the door behind you", "farmer_slain", action_sound="door"),
        ),
    ),
    "dragon_ally": Scene(
        id="dragon_ally",
        title="The Dragon's Chains",
        ambient="spire",
        image="castle",
        text=(
            "You call out to the fire, not to the king, but to what burns "
            "inside it. \"You are not his!\" you shout. \"Be free!\"\n\n"
            "The fire stills. Deep in the stone below the Spire, something "
            "vast and ancient lifts its head."
        ),
        choices=(
            Choice("Let the dragon take its freedom", "good_dragon", action_sound="roar"),
            Choice("Step between the dragon and the king", "both_slain", action_sound="roar"),
        ),
    ),

    # ------------------------------------------------------------- good endings
    "good_punish": Scene(
        id="good_punish",
        title="The King Falls",
        ambient="spire",
        image="castle",
        text=(
            "You seize the fallen torch and drive the king back. He has ruled "
            "by borrowed fire, and fire cannot love him back. His crown "
            "clatters away across the stones.\n\n"
            "The king falls. The court, watching, does not mourn him. You "
            "take Lena's hand, and together you walk out of the Spire, past "
            "the silent guards, into the dawn."
        ),
        choices=(Choice("Play again", "farm", action_sound="steps"),),
        kind="good",
    ),
    "good_break_spell": Scene(
        id="good_break_spell",
        title="The Unmade Spell",
        ambient="spire",
        image="castle",
        text=(
            "You quench the dragon-fire, and the spell-engine dies with a "
            "sound like a long-held breath let out. The veil falls. The "
            "Spire's power goes dark.\n\n"
            "The wizard finds you in the wreckage, and together you write a "
            "new law into the land: no king may ever take a bride by force "
            "again. The stolen fire is given back to the dragon, and the "
            "dragon flies away. And you and Lena go home to a kingdom that "
            "will never fear a king's greed again."
        ),
        choices=(Choice("Play again", "farm", action_sound="steps"),),
        kind="good",
    ),
    "good_escape": Scene(
        id="good_escape",
        title="The Long Road Home",
        ambient="farm",
        image="return",
        text=(
            "You and Lena run until the castle is far behind and the Spire is "
            "only a thin black line on the horizon. You do not stop until you "
            "reach the farm, and the fire is lit, and the door is barred.\n\n"
            "The king can keep his Spire. You have what matters, and you are "
            "never letting go again."
        ),
        choices=(Choice("Play again", "farm", action_sound="steps"),),
        kind="good",
    ),
    "good_dragon": Scene(
        id="good_dragon",
        title="The Dragon Freed",
        ambient="mountain",
        image="road",
        text=(
            "The dragon rises from beneath the Spire and shakes off its "
            "chains. It turns on the king, who has no borrowed fire left to "
            "command, and the Spire comes down in a sheet of light.\n\n"
            "When the dust clears, the king is gone and the dragon is free, "
            "circling once in the morning sky before it flies away. You and "
            "Lena watch it go, hand in hand, and then you walk home."
        ),
        choices=(Choice("Play again", "farm", action_sound="steps"),),
        kind="good",
    ),

    # ------------------------------------------------------------- death endings
    "wife_slain": Scene(
        id="wife_slain",
        title="She Is Gone",
        ambient="spire",
        image="death",
        text=(
            "In the moment you turn away, the king strikes. Lena falls, and "
            "the fire takes her.\n\n"
            "You hold her as the room burns down around you. You do not get "
            "up again."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "both_slain": Scene(
        id="both_slain",
        title="Together",
        ambient="spire",
        image="death",
        text=(
            "You and the king fall together into the fire, and the fire takes "
            "you both. The last thing you know is Lena's hand reaching for "
            "yours, and then nothing."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
    "farmer_slain": Scene(
        id="farmer_slain",
        title="The Door",
        ambient="spire",
        image="death",
        text=(
            "You shove the door closed behind Lena and lean your weight "
            "against it. The fire comes through the wood and the stone and "
            "the smoke, and you hold it as long as you can.\n\n"
            "She is safe. That is enough. It has to be."
        ),
        choices=(Choice("Try again", "farm", action_sound="steps"),),
        kind="death",
    ),
}

START_SCENE = "farm"
DEATH_BELL = "bell"

# Derived terminal sets (kept in sync with each Scene.kind).
DEATH_SCENES = frozenset(sid for sid, s in SCENES.items() if s.kind == "death")
GOOD_ENDINGS = frozenset(sid for sid, s in SCENES.items() if s.kind == "good")


def is_terminal(scene_id):
    return SCENES[scene_id].kind in ("death", "good")


def validate_graph():
    """Return a list of problems; an empty list means the graph is sound."""
    problems = []
    if START_SCENE not in SCENES:
        problems.append("start scene %r missing" % START_SCENE)
    for sid, scene in SCENES.items():
        if scene.kind not in ("scene", "death", "good"):
            problems.append("%s has unknown kind %r" % (sid, scene.kind))
        for i, choice in enumerate(scene.choices):
            if choice.target not in SCENES:
                problems.append(
                    "%s.choices[%d] (%r) -> %r missing" % (sid, i, choice.label, choice.target)
                )
        if scene.kind in ("death", "good"):
            if len(scene.choices) != 1:
                problems.append("%s terminal has %d choices (want 1)" % (sid, len(scene.choices)))
            elif scene.choices[0].target != START_SCENE:
                problems.append("%s restart choice -> %r (want %r)"
                                % (sid, scene.choices[0].target, START_SCENE))
        else:
            if len(scene.choices) < 2:
                problems.append("%s non-terminal has only %d choices" % (sid, len(scene.choices)))
    return problems


class StoryEngine:
    """Pure story navigation (no pygame) - easy to drive from tests."""

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
