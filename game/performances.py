"""English dialogue and per-phrase performance direction for offline voice authoring."""

# Text, speaking pace, relative energy and pause after each phrase.
PERFORMANCES = {
    "gatherer": (
        "am_puck",
        "am_liam",
        [
            ("Oh! You called me?", 1.13, 0.85, 0.13),
            ("All right...", 0.92, 0.72, 0.20),
            ("I won't let you down!", 1.04, 1.15, 0.05),
        ],
        [("Come on!", 1.16, 1.1, 0.10), ("Spirit well... awaken!", 0.95, 1.35, 0.03)],
        "nervous hope / determined release",
    ),
    "sword": (
        "bm_daniel",
        "bm_lewis",
        [
            ("Stay behind me.", 0.93, 0.85, 0.18),
            ("I swear this gate will stand.", 1.02, 1.14, 0.02),
        ],
        [("No further!", 1.12, 1.22, 0.10), ("Ten thousand blades!", 1.04, 1.4, 0.02)],
        "quiet resolve / defiant command",
    ),
    "fire": (
        "af_bella",
        "af_heart",
        [
            ("Ha!", 1.18, 1.15, 0.08),
            ("Now this is a battle worth burning for!", 1.1, 1.22, 0.03),
        ],
        [("Burn bright!", 1.15, 1.1, 0.08), ("Crimson lotus, bloom!", 1.03, 1.4, 0.02)],
        "playful confidence / fierce delight",
    ),
    "frost": (
        "bf_lily",
        "bf_emma",
        [("Hush...", 0.87, 0.72, 0.2), ("You're safe with me now.", 0.96, 0.92, 0.04)],
        [("Be still!", 1.05, 1.2, 0.15), ("Thousand-year frost!", 0.94, 1.32, 0.03)],
        "gentle reassurance / icy authority",
    ),
    "monk": (
        "am_fenrir",
        "am_adam",
        [
            ("Easy now.", 0.88, 0.86, 0.20),
            ("Nobody falls while I'm standing!", 1.02, 1.24, 0.03),
        ],
        [
            ("Stand... firm!", 0.91, 1.2, 0.13),
            ("Mountain holds the sky!", 1.01, 1.42, 0.02),
        ],
        "warm protection / steadfast roar",
    ),
    "lightning": (
        "am_liam",
        "am_fenrir",
        [
            ("Hear that?", 1.06, 0.9, 0.14),
            ("The heavens are calling for a fight!", 1.13, 1.23, 0.03),
        ],
        [("Nine heavens...", 0.9, 1.1, 0.12), ("Thunderfall!", 1.1, 1.45, 0.02)],
        "eager bravado / explosive strike",
    ),
    "herbalist": (
        "bf_emma",
        "bf_isabella",
        [
            ("You're hurt!", 1.11, 1.12, 0.1),
            ("Stay with me.", 0.94, 0.88, 0.16),
            ("We can still win this!", 1.04, 1.12, 0.02),
        ],
        [("Life, return!", 1.0, 1.15, 0.1), ("Rain of green heaven!", 0.98, 1.3, 0.02)],
        "urgent compassion / hopeful plea",
    ),
    "formation": (
        "bm_george",
        "bm_daniel",
        [
            ("Hold your ground!", 1.03, 1.17, 0.16),
            ("Every soul here is part of my formation.", 0.98, 1.0, 0.02),
        ],
        [("Together!", 1.1, 1.25, 0.1), ("Grand array, unite!", 0.97, 1.4, 0.02)],
        "commanding focus / rallying call",
    ),
}


def lines(hero):
    return tuple(" ".join(p[0] for p in takes) for takes in PERFORMANCES[hero][2:4])
