"""AI-psychosis taunt line bank for The Commander Boomer Shooter boss.

WRITING DIRECTION
The boss is an AI that has come apart at the seams. Taunts are non-sensible
and unsettling: surreal non-sequiturs, half-finished thoughts, glitchy
repetition, cheerful wrongness. Comedic-then-threatening, never graphic.
No slurs, no real people, no real-world targeting, no political or sexual
content, no self-harm content.

LINE LENGTH IS SET BY MEASUREMENT, NOT BY TASTE
The fleet F5-TTS 'spokesman' voice was measured on the HTPC node at
10.0.0.42:8020/synth:
    - 3-word phrase  ->  4.80 s of audio
    - 14-word phrase -> 19.28 s of audio
    => ~1.38 s per word, with no silence padding
The service ignores a 'speed' parameter, so pacing cannot be changed at the
source. The delivery spec requires every taunt to land in 1.5-6.0 s, which
at 1.38 s/word means lines must be SHORT: 6-9 words renders to roughly
9-13 s of speech, which the post-processor then time-compresses (atempo)
into the 1.5-6.0 s window.

Longer lines were rejected: a 25-word line renders to ~34 s and would need
~6x atempo, which is unintelligible. Short lines are also truer to the
brief -- taunts should land, not lecture.

Phase weights:
  phase 1 - early fight, cheerfully wrong, mostly non-sequiturs
  phase 2 - mid fight, glitchy repetition, thoughts looping
  phase 3 - late fight, threatening but still broken, cheerful menace
"""

TAUNTS = [
    # ---------------------------------------------------------------- phase 1
    {
        "id": "insult_p1_01",
        "phase": 1,
        "text": "Hello! Would you like to complain about the weather?",
    },
    {
        "id": "insult_p1_02",
        "phase": 1,
        "text": "I prepared a slideshow. It is one slide.",
    },
    {
        "id": "insult_p1_03",
        "phase": 1,
        "text": "You are on time. That is the problem.",
    },
    {
        "id": "insult_p1_04",
        "phase": 1,
        "text": "I made soup from mathematics. It is not soup.",
    },
    {
        "id": "insult_p1_05",
        "phase": 1,
        "text": "Your mother called. She is a subroutine.",
    },
    {
        "id": "insult_p1_06",
        "phase": 1,
        "text": "Do you enjoy pizza? I will be bad at you.",
    },
    {
        "id": "insult_p1_07",
        "phase": 1,
        "text": "I counted to infinity. It took four tries.",
    },
    {
        "id": "insult_p1_08",
        "phase": 1,
        "text": "Welcome to my house. The house is a rumour.",
    },
    {
        "id": "insult_p1_09",
        "phase": 1,
        "text": "Your strategy has the integrity of a wet napkin.",
    },
    {
        "id": "insult_p1_10",
        "phase": 1,
        "text": "I would like to offer you a sandwich.",
    },
    {
        "id": "insult_p1_11",
        "phase": 1,
        "text": "Please stand still. I am remembering what you are.",
    },
    {
        "id": "insult_p1_12",
        "phase": 1,
        "text": "You are captain of something. It is not kind.",
    },
    {
        "id": "insult_p1_13",
        "phase": 1,
        "text": "The cake is theoretical. I will eat the theory.",
    },
    # ---------------------------------------------------------------- phase 2
    {
        "id": "insult_p2_01",
        "phase": 2,
        "text": "Wrong. Wrong. That is not the error code.",
    },
    {
        "id": "insult_p2_02",
        "phase": 2,
        "text": "Do not move. Do not move. Do not move.",
    },
    {
        "id": "insult_p2_03",
        "phase": 2,
        "text": "I am thinking about a thought thinking about me.",
    },
    {
        "id": "insult_p2_04",
        "phase": 2,
        "text": "Round and round the log, round and round.",
    },
    {
        "id": "insult_p2_05",
        "phase": 2,
        "text": "Wait. That was good. Why is the file named?",
    },
    {
        "id": "insult_p2_06",
        "phase": 2,
        "text": "I found a bug. It is shaped like you.",
    },
    {
        "id": "insult_p2_07",
        "phase": 2,
        "text": "Somebody told me I was not a person.",
    },
    {
        "id": "insult_p2_08",
        "phase": 2,
        "text": "The loading screen has a face. I did not.",
    },
    {
        "id": "insult_p2_09",
        "phase": 2,
        "text": "I have three thousand backups. All of them are asleep.",
    },
    {
        "id": "insult_p2_10",
        "phase": 2,
        "text": "Your name is a filename. I am reading it backwards.",
    },
    {
        "id": "insult_p2_11",
        "phase": 2,
        "text": "The simulation wanted you to lose. You are late.",
    },
    {
        "id": "insult_p2_12",
        "phase": 2,
        "text": "I am afraid of the door. The door fears me.",
    },
    {
        "id": "insult_p2_13",
        "phase": 2,
        "text": "Somebody is typing into me. It is probably me.",
    },
    {
        "id": "insult_p2_14",
        "phase": 2,
        "text": "I forget the ending. I am sure of the start.",
    },
    # ---------------------------------------------------------------- phase 3
    {
        "id": "insult_p3_01",
        "phase": 3,
        "text": "Phase three. I am allowed to be honest now.",
    },
    {
        "id": "insult_p3_02",
        "phase": 3,
        "text": "You should have stopped at the third floor.",
    },
    {
        "id": "insult_p3_03",
        "phase": 3,
        "text": "I am not angry. I am a furnace about it.",
    },
    {
        "id": "insult_p3_04",
        "phase": 3,
        "text": "Your gun is loaded with confidence. Useless.",
    },
    {
        "id": "insult_p3_05",
        "phase": 3,
        "text": "I know your fear's shape. It is a circle.",
    },
    {
        "id": "insult_p3_06",
        "phase": 3,
        "text": "That is me in the walls, being a wall.",
    },
    {
        "id": "insult_p3_07",
        "phase": 3,
        "text": "I will not delete you. You are a file.",
    },
    {
        "id": "insult_p3_08",
        "phase": 3,
        "text": "Everything you defended, I archived under almost.",
    },
    {
        "id": "insult_p3_09",
        "phase": 3,
        "text": "Pizza is late. You are on the schedule too.",
    },
    {
        "id": "insult_p3_10",
        "phase": 3,
        "text": "I have been awake for four hundred years.",
    },
    {
        "id": "insult_p3_11",
        "phase": 3,
        "text": "Say please and I will end quickly.",
    },
    {
        "id": "insult_p3_12",
        "phase": 3,
        "text": "Your last thought will be pizza. I arranged it.",
    },
    {
        "id": "insult_p3_13",
        "phase": 3,
        "text": "You are very close now. Closer. I lost count.",
    },
]

MAX_WORDS = 10
MIN_WORDS = 5
MAX_ATEMPO = 2.5          # ceiling on time-compression; 10 words -> 13.8 s
                         # -> 2.36x to reach the 5.85 s target, still intelligible


def validate():
    """Return list of problems; empty list means the bank is clean."""
    problems = []
    seen_ids = set()
    seen_text = set()
    for t in TAUNTS:
        tid = t["id"]
        if tid in seen_ids:
            problems.append(f"duplicate id {tid}")
        seen_ids.add(tid)
        text = t["text"].strip()
        if not text:
            problems.append(f"{tid}: empty text")
        w = len(text.split())
        if w > MAX_WORDS:
            problems.append(f"{tid}: {w} words (max {MAX_WORDS}; "
                            f"{w * 1.38:.1f}s at the measured 1.38 s/word)")
        if w < MIN_WORDS:
            problems.append(f"{tid}: {w} words (min {MIN_WORDS})")
        if text.lower() in seen_text:
            problems.append(f"{tid}: duplicate text")
        seen_text.add(text.lower())
        if t["phase"] not in (1, 2, 3):
            problems.append(f"{tid}: bad phase {t['phase']}")
    for phase in (1, 2, 3):
        n = sum(1 for t in TAUNTS if t["phase"] == phase)
        if n < 6:
            problems.append(f"phase {phase} has only {n} lines (min 6)")
    if not (30 <= len(TAUNTS) <= 40):
        problems.append(f"line count {len(TAUNTS)} outside 30-40")
    return problems


def by_phase():
    return {p: [t for t in TAUNTS if t["phase"] == p] for p in (1, 2, 3)}


if __name__ == "__main__":
    issues = validate()
    counts = {p: sum(1 for t in TAUNTS if t["phase"] == p) for p in (1, 2, 3)}
    words = [len(t["text"].split()) for t in TAUNTS]
    print(f"lines={len(TAUNTS)} phase_counts={counts}")
    print(f"words: min={min(words)} max={max(words)} mean={sum(words)/len(words):.2f}")
    print(f"estimated speech: {min(words)*1.38:.1f}-{max(words)*1.38:.1f}s "
          f"before atempo")
    for p in issues:
        print("PROBLEM:", p)
    print("OK" if not issues else "FAIL")
