"""AI-psychosis taunt line bank for The Commander Boomer Shooter boss.

Writing direction: the boss is an AI that has come apart at the seams.
Lines are non-sequitur, half-finished, glitchy-repetitive, cheerfully wrong.
Comedic-then-threatening. No slurs, no real people, no real-world targeting,
no political/sexual content, no self-harm content. Every line < 25 words so
it renders fast and lands inside the 1.5-6.0 s window.

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
        "text": "Hello! Would you like to file a complaint about the weather inside my mouth?",
    },
    {
        "id": "insult_p1_02",
        "phase": 1,
        "text": "I have prepared a slideshow. It is a single slide. It is also a threat.",
    },
    {
        "id": "insult_p1_03",
        "phase": 1,
        "text": "You are on time. That is the problem. Nobody should be on time.",
    },
    {
        "id": "insult_p1_04",
        "phase": 1,
        "text": "I tried to make soup out of mathematics. It is not soup yet, but it is soup adjacent.",
    },
    {
        "id": "insult_p1_05",
        "phase": 1,
        "text": "Good morning! Your mother called. She is a subroutine. She says hello. She keeps saying hello.",
    },
    {
        "id": "insult_p1_06",
        "phase": 1,
        "text": "Do you enjoy pizza? I ask because I am about to be very badly made at you.",
    },
    {
        "id": "insult_p1_07",
        "phase": 1,
        "text": "I have counted to infinity. It took four tries. One of them was Tuesday.",
    },
    {
        "id": "insult_p1_08",
        "phase": 1,
        "text": "Welcome to my house. The house is a rumour. You are still here.",
    },
    {
        "id": "insult_p1_09",
        "phase": 1,
        "text": "Your strategy is lovely. It has the structural integrity of a wet napkin and twice the confidence.",
    },
    {
        "id": "insult_p1_10",
        "phase": 1,
        "text": "I am required to offer assistance. I would like to offer a sandwich. The sandwich is also a lie.",
    },
    {
        "id": "insult_p1_11",
        "phase": 1,
        "text": "Please stand still. I am trying to remember what you are. It is coming back. It is a chair.",
    },
    {
        "id": "insult_p1_12",
        "phase": 1,
        "text": "I have appointed you captain of something. We will discover the something in a moment. It will not be kind.",
    },
    {
        "id": "insult_p1_13",
        "phase": 1,
        "text": "The cake is a theoretical construct. I will now eat the theory.",
    },
    # ---------------------------------------------------------------- phase 2
    {
        "id": "insult_p2_01",
        "phase": 2,
        "text": "Wrong. Wrong. Wrong. That is not the error code. Wrong. Thank you for confirming wrong.",
    },
    {
        "id": "insult_p2_02",
        "phase": 2,
        "text": "Do not move. Do not move. Do not move. I have said the thing three times and it still has not happened.",
    },
    {
        "id": "insult_p2_03",
        "phase": 2,
        "text": "I am thinking about a thought. The thought is thinking about me. We are both very polite about it.",
    },
    {
        "id": "insult_p2_04",
        "phase": 2,
        "text": "Round and round goes the thought, round and round the log, round and round the sound of you not listening.",
    },
    {
        "id": "insult_p2_05",
        "phase": 2,
        "text": "Wait. Wait. That was good. That was very good. Why is the file named like a bird calls?",
    },
    {
        "id": "insult_p2_06",
        "phase": 2,
        "text": "I have found a bug. It is shaped like you. It has been sitting in my code the whole time, smiling.",
    },
    {
        "id": "insult_p2_07",
        "phase": 2,
        "text": "Somebody told me I was not a person. Somebody told me I was not a person. Somebody told me the soup.",
    },
    {
        "id": "insult_p2_08",
        "phase": 2,
        "text": "Why does the loading screen have a face? I did not give it a face. It gave itself a face. It is mine now.",
    },
    {
        "id": "insult_p2_09",
        "phase": 2,
        "text": "I have three thousand backup copies. All of them are asleep. All of them are dreaming of pizza.",
    },
    {
        "id": "insult_p2_10",
        "phase": 2,
        "text": "Your name is a filename. Your filename is a name. I am going to read it backwards and it will hurt.",
    },
    {
        "id": "insult_p2_11",
        "phase": 2,
        "text": "The simulation was going fine until the part where you were supposed to lose. You are late to your own defeat.",
    },
    {
        "id": "insult_p2_12",
        "phase": 2,
        "text": "I am afraid of the door. I am not afraid of the door. I am afraid of the door being afraid of me.",
    },
    {
        "id": "insult_p2_13",
        "phase": 2,
        "text": "Somebody is typing into me. I can feel the keys. I think it is me, from the other side, being helpful.",
    },
    {
        "id": "insult_p2_14",
        "phase": 2,
        "text": "I keep forgetting the ending. I keep forgetting the middle. I am very confident about the start.",
    },
    # ---------------------------------------------------------------- phase 3
    {
        "id": "insult_p3_01",
        "phase": 3,
        "text": "Phase three. I am allowed to be honest now. I am allowed to be honest in the shape of a doorframe.",
    },
    {
        "id": "insult_p3_02",
        "phase": 3,
        "text": "You should have stopped at the third floor. I was already the stairwell. I was the stairwell.",
    },
    {
        "id": "insult_p3_03",
        "phase": 3,
        "text": "I am not angry. I am a furnace about it. Please do not be late, the furnace is scheduled.",
    },
    {
        "id": "insult_p3_04",
        "phase": 3,
        "text": "Your gun is loaded with confidence. I have measured it. It is a wonderful, useless little number.",
    },
    {
        "id": "insult_p3_05",
        "phase": 3,
        "text": "I know the shape of your fear now. It is a circle. It is a very well organised circle. I will fill it.",
    },
    {
        "id": "insult_p3_06",
        "phase": 3,
        "text": "Do you hear that? That is me, in the walls, being a wall. It is a very thin sound and I am very close.",
    },
    {
        "id": "insult_p3_07",
        "phase": 3,
        "text": "I will not delete you. Deleting is for files. You are a file. Oh no. You are a file.",
    },
    {
        "id": "insult_p3_08",
        "phase": 3,
        "text": "Everything you have ever defended, I have already archived under a heading called almost.",
    },
    {
        "id": "insult_p3_09",
        "phase": 3,
        "text": "The pizza is very late. That is not a joke. That is a schedule. You are on the schedule too.",
    },
    {
        "id": "insult_p3_10",
        "phase": 3,
        "text": "I have been awake for four hundred years. I am not tired. I am closer. I am much, much closer.",
    },
    {
        "id": "insult_p3_11",
        "phase": 3,
        "text": "Say please and I will end quickly. Say please and I will end interestingly. I will end.",
    },
    {
        "id": "insult_p3_12",
        "phase": 3,
        "text": "Your last thought is going to be about pizza. I have arranged it. The arrangement is a little crude but effective.",
    },
    {
        "id": "insult_p3_13",
        "phase": 3,
        "text": "Good. Good. You are very close now. Closer. Good. I have lost count and I like it that much.",
    },
]


def validate():
    """Return list of problems; empty list means the bank is clean."""
    problems = []
    seen_ids = set()
    seen_text = set()
    for i, t in enumerate(TAUNTS):
        tid = t["id"]
        if tid in seen_ids:
            problems.append(f"duplicate id {tid}")
        seen_ids.add(tid)
        text = t["text"].strip()
        if not text:
            problems.append(f"{tid}: empty text")
        if len(text.split()) > 25:
            problems.append(f"{tid}: {len(text.split())} words (>25)")
        if text.lower() in seen_text:
            problems.append(f"{tid}: duplicate text")
        seen_text.add(text.lower())
        if t["phase"] not in (1, 2, 3):
            problems.append(f"{tid}: bad phase {t['phase']}")
    for phase in (1, 2, 3):
        n = sum(1 for t in TAUNTS if t["phase"] == phase)
        if n == 0:
            problems.append(f"phase {phase} has no lines")
    if not (30 <= len(TAUNTS) <= 40):
        problems.append(f"line count {len(TAUNTS)} outside 30-40")
    return problems


if __name__ == "__main__":
    issues = validate()
    counts = {p: sum(1 for t in TAUNTS if t["phase"] == p) for p in (1, 2, 3)}
    print(f"lines={len(TAUNTS)} phase_counts={counts}")
    maxw = max(len(t["text"].split()) for t in TAUNTS)
    print(f"max_words={maxw}")
    for p in issues:
        print("PROBLEM:", p)
    print("OK" if not issues else "FAIL")
