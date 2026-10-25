"""Original campaign and optional exploration stories. No combat rewards are minted here."""

from copy import deepcopy

SIDE_NPCS = [
    dict(
        id="mei",
        name="Mei",
        title="River Boatwoman",
        x=220,
        y=200,
        topics=[
            (
                "The empty boats",
                "I brought the last ferry up before dawn. My brother stayed to light the landing lamps. I keep counting the empty seats, as if that will tell me where he is.",
            ),
            (
                "What do you need?",
                "A harbor is not saved by defeating its lord alone. The people need a way home. Tell me when the river bells ring clearly again.",
            ),
        ],
        after="The bells rang. My brother is mending the ferry, and the first passengers are bringing seed upstream. We still do not know who woke the river lord, but now we can ask that question together.",
    ),
    dict(
        id="tao",
        name="Master Tao",
        title="Lantern Artisan",
        x=335,
        y=155,
        topics=[
            (
                "Why are your lamps blue?",
                "A lantern remembers the wish written inside it. These ones turned blue before the river rose. Someone altered the ink sent down from the mountain.",
            ),
            (
                "The missing shipment",
                "Qiao carried the mountain seal on the last crate. She did not pack it. Ask her about the broken bridge before you accuse her of anything.",
            ),
        ],
        after="You brought a true flame back from the palace. I can remake the lamps now. A repaired lamp is useful; a repaired trust is harder. Give Qiao time.",
    ),
    dict(
        id="qiao",
        name="Qiao",
        title="Mountain Envoy",
        x=335,
        y=115,
        topics=[
            (
                "The mountain road",
                "The terraces once fed every village below. Their channels are carrying cold ash now. If you follow that water, you will reach the place where our wardens stopped speaking to each other.",
            ),
            (
                "Your seal on the crate",
                "Yes, it is mine. I signed for clean jade dust, then the road collapsed behind me. I have been afraid that defending myself would sound like abandoning the people who suffered.",
            ),
        ],
        after="The channels run clear. The mountain lord remembered his oath when you broke the seal around him. He named the old court, beyond the ancestral valley. I will guide anyone willing to hear its witnesses.",
    ),
    dict(
        id="lin",
        name="Uncle Lin",
        title="Keeper of the Fields",
        x=149,
        y=184,
        topics=[
            (
                "Why grow herbs now?",
                "Because someone must prepare for the people who return. A little tea can be a plan for tomorrow. These fields count journeys, not hours; nothing here will wither because you took a rest.",
            ),
            (
                "Your first lesson",
                "Plant, water, then let a real expedition pass. Look at the leaves when you return. Better soil helps a harvest; tugging on a seedling does not help it grow.",
            ),
        ],
        after="You have brought someone home from every road. Leave a little space in the garden. Travelers have a habit of arriving with seeds we have never seen.",
    ),
    dict(
        id="suyin",
        name="Suyin",
        title="Listener of Forgotten Names",
        x=290,
        y=113,
        topics=[
            (
                "The paper cranes",
                "They carry names the court struck from its records. Some belong to the dead. Some belong to people still waiting for a letter. A spirit is not always asking to be defeated.",
            ),
            (
                "The ancestral valley",
                "Read the names by the sealed gate before you answer its bell. The emperor made obedience sound like remembrance. We can remember people without keeping them in chains.",
            ),
        ],
        after="The court is quiet, and the names have voices again. Some spirits chose the road home. Others asked me to keep their stories. The last crane still points toward an uncharted northern pass.",
    ),
    dict(
        id="ren",
        name="Ren",
        title="Courier Between the Roads",
        x=284,
        y=229,
        topics=[
            (
                "Any news?",
                "Letters arrive with mud, ash and petals folded between the pages. The people in them disagree about the cause of the fracture. That is why I carry all of them.",
            ),
            (
                "A road worth writing",
                "Walk the grounds and notice three small things. A flower, a lamp, an old stone. If our letters only describe battles, no one will remember what the battles were meant to protect.",
            ),
        ],
        after="The road is open, but the letters have not stopped. I have requests from villages outside this map. We have time to read them before we decide where the next road should go.",
    ),
]
NPC_BY_ID = {n["id"]: n for n in SIDE_NPCS}


def chapter(
    id, title, region, x, y, speaker, location, reason, pages, choices, aftermath
):
    return dict(
        id=id,
        title=title,
        region=region,
        x=x,
        y=y,
        speaker=speaker,
        location=location,
        reason=reason,
        pages=pages,
        choices=[dict(id=k, label=l, response=r) for k, l, r in choices],
        aftermath=aftermath,
    )


CHAPTERS = [
    chapter(
        "wharf-1",
        "A Light for the Returning",
        "wharf",
        14,
        72,
        "mei",
        "Ferry Landing",
        "Keep the landing open while the last ferries reach shore.",
        [
            "The river rose without rain. Mei has brought one ferry to the mountain, but her brother and the night watch remain at the landing.",
            "The first lamps are failing. Hold the shore long enough for the watch to light a safe channel; the harbor cannot evacuate into darkness.",
            "Mei offers two tasks for the people waiting behind your line. Both can help the harbor remember that it is still a home.",
        ],
        [
            (
                "lanterns",
                "Ask the watch to relight the lamps",
                "Mei sends the watch to the lamp posts. When the first ferry returns, its passengers will see a path instead of an empty shore.",
            ),
            (
                "families",
                "Ask the ferrymen to find the missing families",
                "Mei starts a list of names on the ferry ledger. The search will follow the lamps once your line holds.",
            ),
        ],
        "The first ferry reaches shore. Mei finds her brother alive among the lamp keepers. In a damaged lantern, Tao discovers ink bearing a mountain seal.",
    ),
    chapter(
        "wharf-2",
        "Ink Beneath the Lanterns",
        "wharf",
        23,
        51,
        "tao",
        "Lantern Bridge",
        "Protect the bridge while Tao uncovers the source of the corrupted lamp ink.",
        [
            "Tao spreads a blue-stained wick on the bridge. The flame burns cold even after he replaces the oil.",
            "The ink was made with jade dust from the Azure Terrace. Before you can follow the shipment, you must hold the crossing against the returning drowned.",
            "A courier waits beside the bridge. Choose what message should travel ahead of the party.",
        ],
        [
            (
                "warning",
                "Send a warning to the mountain villages",
                "Ren carries a practical warning: close the poisoned channels and keep the village lamps burning.",
            ),
            (
                "question",
                "Ask the mountain wardens for their account",
                "Ren carries a question, without an accusation. Someone may speak before fear closes the mountain gates.",
            ),
        ],
        "Tao finds a second seal under the first: an old court mark. The river palace bell answers it. The lord inside is bound to an oath he no longer understands.",
    ),
    chapter(
        "wharf-3",
        "The River Lord's Oath",
        "wharf",
        31,
        28,
        "mei",
        "River Palace",
        "Break the river palace siege and free the harbor from its drowned oath.",
        [
            "Mei brings you to the palace steps. She remembers this lord guiding ferries through spring floods, long before the lamps turned blue.",
            "Tao believes the bell is repeating a command from the ancestral court. Defeat the force holding the palace; the river cannot carry anyone home until it is silenced.",
            "Before the line forms, Mei asks what should be done with the bell afterward.",
        ],
        [
            (
                "keep",
                "Keep the bell as a witness",
                "Mei will bring the broken bell to Suyin. Even a cruel command can leave evidence of the person who gave it.",
            ),
            (
                "quiet",
                "Let the harbor choose its own quiet",
                "Mei will ask the families whether to keep or bury the bell. Their home deserves a voice in what is remembered.",
            ),
        ],
        "The oath breaks and the tide settles. The river lord points toward poisoned water falling from the Azure Terrace. Qiao offers to guide the next journey.",
    ),
    chapter(
        "terrace-1",
        "The Garden That Forgot Spring",
        "terrace",
        43,
        67,
        "qiao",
        "Lower Ley Gardens",
        "Keep the gardeners safe while the first corrupted ley channels are purified.",
        [
            "The mountain gardens are flowering out of season. Their roots hold grey water instead of sap.",
            "Qiao recognizes the delivery route, but not the court seal on its crates. Mu Qing needs a defended work area to test the channels and recover living seed.",
            "A gardener points to two damaged channels. Decide what you want the village to learn from this first repair.",
        ],
        [
            (
                "restore",
                "Restore a channel the villagers can share",
                "Qiao asks the gardeners to work together at the common channel. The repair will be a lesson they can repeat after you leave.",
            ),
            (
                "trace",
                "Trace the corruption before closing the breach",
                "Qiao marks the old warding script before the channel is cleansed. Suyin may recognize the hand that wrote it.",
            ),
        ],
        "Clean water reaches the lower gardens. The villagers find court script beneath the ley stones. Above them, sky hunters gather at the broken bridge.",
    ),
    chapter(
        "terrace-2",
        "The Bridge of Unsent Letters",
        "terrace",
        51,
        43,
        "ren",
        "Cloudspan Crossing",
        "Hold the cloud bridge so the couriers and wounded gardeners can cross.",
        [
            "Ren arrives with letters that never reached the upper terraces. Some warn of the poisoned dust; others beg the wardens to stop blaming the river villages.",
            "Flying hunters circle the crossing. Keep every approach covered while the villagers carry their records and wounded across the cloud bridge.",
            "One packet bears the mountain lord's private seal. Ren asks whether to deliver it openly.",
        ],
        [
            (
                "open",
                "Let the witnesses read the packet together",
                "Ren opens the packet before the village elders. Its words will belong to everyone who has paid for their silence.",
            ),
            (
                "private",
                "Carry it to the lord with its seal intact",
                "Ren keeps the seal. You will give the lord a chance to answer before the villages decide what his letter means.",
            ),
        ],
        "The packet describes an oath that once linked river, mountain and tomb. Its final clause was erased. The mountain lord guards the only surviving copy.",
    ),
    chapter(
        "terrace-3",
        "A Warden Above the Clouds",
        "terrace",
        60,
        24,
        "qiao",
        "Sky Pavilion",
        "Break the mountain lord's binding and recover the final clause of the old oath.",
        [
            "Qiao has walked these steps since childhood. The lord at their summit now speaks with the same measured cadence as the river bell.",
            "His corrupted wards will not yield to an argument. Hold the pavilion and break the power around him without abandoning the gardeners below.",
            "Qiao asks how the recovered oath should be carried into the ancestral valley.",
        ],
        [
            (
                "witnesses",
                "Bring the living witnesses with the text",
                "Qiao records the names of river and mountain witnesses. The court will hear people as well as a document.",
            ),
            (
                "copy",
                "Make copies before anyone enters the tomb",
                "Qiao gives Ren a copy for each village. Whatever happens in the valley, the truth will not depend on one scroll surviving.",
            ),
        ],
        "Freed from the binding, the lord names the Bone Court. The erased clause gave ordinary people the right to end the oath. Suyin knows where their names were buried.",
    ),
    chapter(
        "tomb-1",
        "The Gate of Missing Names",
        "tomb",
        71,
        70,
        "suyin",
        "Ancestral Gate",
        "Defend the sealed entrance while Suyin restores the names that can open it.",
        [
            "At the tomb gate, Suyin unfolds cranes made from rejected records. Each carries a name the emperor removed from the oath.",
            "The gate admits commands but no witnesses. Hold the approach while Suyin reads the missing names back into its stones.",
            "Some spirits fear being called. Choose how to invite them to the hearing.",
        ],
        [
            (
                "invite",
                "Invite each spirit to speak or remain silent",
                "Suyin leaves room between the names. Remembering someone will not become another order they are forced to obey.",
            ),
            (
                "record",
                "Offer to carry their testimony in writing",
                "Suyin places blank paper at the gate. A spirit may leave a few words without having to face the court itself.",
            ),
        ],
        "The gate opens for a name that was never a title: the first ferryman who signed the oath. Inside, false funeral pyres are burning the records still bound to it.",
    ),
    chapter(
        "tomb-2",
        "The Pyres of Borrowed Voices",
        "tomb",
        80,
        48,
        "suyin",
        "Spirit Pyres",
        "Protect the surviving records and silence the pyres that force the dead to repeat the oath.",
        [
            "The pyres do not burn bodies. They burn stories, leaving only the words the emperor wishes the dead to repeat.",
            "Suyin and Tao can separate the witness records from the bindings. They need time behind your line before the next funeral flame catches.",
            "Among the records is a frightened scribe's confession. Decide how it will be kept.",
        ],
        [
            (
                "include",
                "Keep the confession beside the other accounts",
                "Suyin will record the harm and the fear together. A complete account need not excuse the person who wrote it.",
            ),
            (
                "hear",
                "Ask the survivors to answer the confession",
                "Suyin leaves a place for the survivors' words. The scribe will not be the only person allowed to describe what happened.",
            ),
        ],
        "The false pyres go dark. The surviving witnesses can now end the oath, but the emperor has gathered its remaining power inside the court.",
    ),
    chapter(
        "tomb-3",
        "An Oath No One Must Keep",
        "tomb",
        89,
        24,
        "suyin",
        "Bone Court",
        "Defend the witnesses and break the emperor's power over the three lands.",
        [
            "Mei, Qiao and Suyin stand before the court with names, letters and the recovered clause. The emperor calls their testimony a breach of order.",
            "The oath was meant to protect the roads. It became a cage when its keeper erased the right to leave. Hold the final line while the witnesses revoke it.",
            "Before the court awakens, the witnesses ask what should stand where the old oath once stood.",
        ],
        [
            (
                "council",
                "Let the villages write a new agreement together",
                "The witnesses will return home with a question instead of a command. A new agreement must allow those who live under it to change it.",
            ),
            (
                "openroad",
                "Leave the road unbound while trust returns",
                "The witnesses will keep the roads open without a new binding. Trust may grow more slowly than a spell, but it can be freely given.",
            ),
        ],
        "The emperor falls and the binding ends. The three lands begin their own conversations. Ren brings a letter from an uncharted northern pass; for now, you can rest, tend the garden and hear the stories that survived.",
    ),
]
CHAPTER_BY_ID = {c["id"]: c for c in CHAPTERS}

OBSERVATIONS = [
    dict(
        id="blossom",
        name="Wish Blossoms",
        x=220,
        y=218,
        prop="flower",
        kind="flower",
        text="A ribbon tied to this branch asks for a safe return, not a victory. The petals stir when you brush them.",
    ),
    dict(
        id="grass",
        name="Windgrass",
        x=330,
        y=196,
        prop="grass",
        kind="grass",
        text="The blades bend under your hand and slowly rise again. Lin says healthy grass tells you where yesterday's rain settled.",
    ),
    dict(
        id="lotus",
        name="Fountain Lotus",
        x=236,
        y=180,
        prop="flower",
        kind="water",
        text="Ripples reach the lotus before the bell sounds. A small plaque reads: leave the water clear for the next traveler.",
    ),
    dict(
        id="chimes",
        name="Old Jade Chimes",
        x=142,
        y=184,
        prop="chime",
        kind="chime",
        text="Three notes answer one another: river, mountain and valley. The quiet fourth note has no inscription.",
    ),
    dict(
        id="stone",
        name="Worn Oath Stone",
        x=286,
        y=192,
        prop="spring",
        kind="stone",
        text="Many hands have polished this stone. Beneath a formal oath someone carved a much simpler promise: we will listen.",
    ),
    dict(
        id="board",
        name="A Letter in the Wind",
        x=205,
        y=160,
        prop="seeds",
        kind="letter",
        text="Ren has pinned a half-finished letter here. It describes the smell of garden soil after rain, then leaves a blank line for someone else.",
    ),
    dict(
        id="spring",
        name="Clear Spring",
        x=362,
        y=214,
        prop="spring",
        kind="water",
        text="You cup your hands under the cold spring. It comes from the same mountain as the water that feeds the three lands.",
    ),
    dict(
        id="lantern",
        name="Unwritten Lantern",
        x=335,
        y=172,
        prop="trellis",
        kind="lantern",
        text="Tao left this lantern unwritten. There is room for a wish that has not been chosen for you.",
    ),
    dict(
        id="crane",
        name="Resting Paper Crane",
        x=302,
        y=109,
        prop="chime",
        kind="crane",
        text="The crane unfolds just enough to show one word: home. It folds again when you step back.",
    ),
    dict(
        id="reeds",
        name="Travelers' Reeds",
        x=390,
        y=207,
        prop="grass",
        kind="grass",
        text="A little path runs through these reeds. Someone has taken the long way to the market to enjoy the view.",
    ),
]
OBSERVATION_BY_ID = {o["id"]: o for o in OBSERVATIONS}
FAVORS = [
    dict(
        id="courier",
        npc="ren",
        title="A Road Worth Writing",
        description="Notice three different details around the sanctuary.",
        target=3,
        kind="observations",
        keepsake="A letter with room for your own words",
    ),
    dict(
        id="gardener",
        npc="lin",
        title="Something for Tomorrow",
        description="Harvest one crop from the Spirit Fields.",
        target=1,
        kind="harvests",
        keepsake="A pressed flower from Lin's first garden",
    ),
    dict(
        id="river",
        npc="mei",
        title="When the Bells Ring Clearly",
        description="Complete the River Palace encounter.",
        target=1,
        kind="wharf",
        keepsake="A river knot tied by the returning ferrymen",
    ),
]


CULTIVATOR_TALKS = {
    "gatherer": dict(
        id="gatherer",
        name="Little Daoist Yun",
        title="Garden Apprentice",
        topics=[
            (
                "The first expedition",
                "I used to count how much Qi I could gather. Lin asked me to count how many people could share a cup of tea instead. I am still learning the difference.",
            ),
            (
                "A seed from home",
                "Mei brought a seed wrapped in a ferry ticket. I do not know what it will grow into. May we leave one corner of the garden for it?",
            ),
        ],
    ),
    "sword": dict(
        id="sword",
        name="Shen Zhu",
        title="Sword Instructor",
        topics=[
            (
                "Why stand at the gate?",
                "A sword can open a road, but it cannot decide where people should go. That is why I ask who is waiting on the other side before I draw it.",
            ),
            (
                "A quieter practice",
                "The first lesson in this courtyard is to stop moving without losing your balance. The second is to notice who has been standing beside you.",
            ),
        ],
    ),
    "fire": dict(
        id="fire",
        name="Hong Lian",
        title="Lantern Broker",
        topics=[
            (
                "What the market carries",
                "Seeds, medicine, letters, gossip. A market is one way a village admits it needs its neighbors. I would like these stalls to need one another again.",
            ),
            (
                "Tao and his lamps",
                "Tao always leaves one lantern unpainted. He says a light should not have to know the wish it is carrying. I think he leaves it for himself.",
            ),
        ],
    ),
    "frost": dict(
        id="frost",
        name="Bing Ruo",
        title="Keeper of the Gates",
        topics=[
            (
                "The three roads",
                "The river feeds the mountain gardens; the mountain guards the valley; the valley keeps the names of those who built both. None of them can be healed by pretending it stands alone.",
            ),
            (
                "Why let them choose?",
                "An oath that cannot be refused is only an order wearing ceremonial clothes. Listen to the witnesses before you decide what our defense is meant to protect.",
            ),
        ],
    ),
    "monk": dict(
        id="monk",
        name="Jin Shan",
        title="Keeper of Vows",
        topics=[
            (
                "Promises and commissions",
                "A small promise kept is a useful kind of strength. These commissions are requests from people with lives beyond the gate, not tests of your devotion.",
            ),
            (
                "The old oath",
                "I once believed an unbroken oath was always a good thing. Suyin taught me to ask whose name was missing from it.",
            ),
        ],
    ),
    "lightning": dict(
        id="lightning",
        name="Lei Xun",
        title="Trial Warden",
        topics=[
            (
                "Beyond the trials",
                "I like a difficult road. Ren keeps reminding me that the people who live on it may prefer a safe one. Both are worth making room for.",
            ),
            (
                "The northern pass",
                "A crane arrived from beyond the mountains with no sender. We do not have to chase every mystery today. The letter will still be here after tea.",
            ),
        ],
    ),
    "herbalist": dict(
        id="herbalist",
        name="Mu Qing",
        title="Sect Alchemist",
        topics=[
            (
                "Returning home",
                "Healing does not finish when a battle ends. Someone will need clean water, sleep and a meal they did not have to earn by fighting. The garden is part of that work.",
            ),
            (
                "Mu Qing and the garden",
                "The four herbs we know are a beginning. Every traveler describes another plant. I keep an empty page beside each recipe so their knowledge has somewhere to go.",
            ),
        ],
    ),
    "formation": dict(
        id="formation",
        name="Zhen Luo",
        title="Keeper of Records",
        topics=[
            (
                "What the archive keeps",
                "A record can explain a pattern, or hide the person who broke it. I have started keeping the witnesses’ accounts beside our diagrams.",
            ),
            (
                "The missing clause",
                "The last line of the oath was not lost. Someone removed it. Suyin says a blank space can be evidence if we are willing to ask who made it.",
            ),
        ],
    ),
}


def new_story():
    return dict(choices={}, seen=[], observations=[], met=[], favors=[])


def normalize_story(raw):
    result = new_story()
    if not isinstance(raw, dict):
        return result
    choices = raw.get("choices", {})
    if isinstance(choices, dict):
        result["choices"] = {
            id: choices[id]
            for id, c in CHAPTER_BY_ID.items()
            if isinstance(choices.get(id), str)
            and choices[id] in {v["id"] for v in c["choices"]}
        }
    for key, allowed in [
        ("seen", CHAPTER_BY_ID),
        ("observations", OBSERVATION_BY_ID),
        ("met", NPC_BY_ID),
        ("favors", {f["id"]: f for f in FAVORS}),
    ]:
        if isinstance(raw.get(key), list):
            result[key] = [id for id in allowed if id in raw[key]]
    return result


def chapter_open(profile, id):
    ids = list(CHAPTER_BY_ID)
    return id in CHAPTER_BY_ID and (
        ids.index(id) == 0
        or ids[ids.index(id) - 1] in profile["completed"]
        or id in profile["completed"]
    )


def favor_progress(profile, favor):
    if favor["kind"] == "observations":
        return len(profile["estate"]["story"]["observations"])
    if favor["kind"] == "harvests":
        return profile["estate"]["stats"].get("harvests", 0)
    return int("wharf-3" in profile["completed"])


def public_story():
    return deepcopy(
        dict(
            chapters=CHAPTERS,
            npcs=SIDE_NPCS,
            cultivators=CULTIVATOR_TALKS,
            observations=OBSERVATIONS,
            favors=FAVORS,
        )
    )
