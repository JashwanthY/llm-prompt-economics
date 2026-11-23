"""Study A run order (DESIGN.md §4.2): 48 sessions, fixed by seed 17.

Within each agent the arms strictly alternate, the starting arm drawn from the
seed; the two agents' sequences are interleaved so calendar drift in either
subscription lands on both arms equally.
"""
import random

AGENTS = ("claude", "codex")
PROMPTS = ("P1", "P2", "P3", "P4")
REPS = 3
SEED = 17


def make_schedule(seed=SEED, agents=AGENTS, prompts=PROMPTS, reps=REPS):
    rng = random.Random(seed)
    per_agent = []
    for agent in agents:
        cells = {arm: [(p, r) for p in prompts for r in range(1, reps + 1)] for arm in ("off", "on")}
        for arm in ("off", "on"):
            rng.shuffle(cells[arm])
        first = rng.choice(["off", "on"])
        second = "on" if first == "off" else "off"
        seq = []
        for a, b in zip(cells[first], cells[second]):
            seq += [(first, a), (second, b)]
        per_agent.append([{"run_id": f"A-{agent}-{arm}-{p}-r{r}", "study": "A", "agent": agent,
                           "arm": arm, "prompt_id": p, "rep": r} for arm, (p, r) in seq])
    return [run for group in zip(*per_agent) for run in group]


A2_ARMS = ("off", "on", "instr")
A2_SEED = 18


def make_schedule_a2(seed=A2_SEED, prompts=PROMPTS, reps=REPS):
    """Study A2 run order (DESIGN_A2.md §3): 36 Claude Code sessions, fixed by seed 18.

    Twelve consecutive triplets, each holding one run of every arm in a seeded
    random order, so drift during the window lands on all three arms equally.
    """
    rng = random.Random(seed)
    cells = {arm: [(p, r) for p in prompts for r in range(1, reps + 1)] for arm in A2_ARMS}
    for arm in A2_ARMS:
        rng.shuffle(cells[arm])
    out = []
    for i in range(len(prompts) * reps):
        order = list(A2_ARMS)
        rng.shuffle(order)
        for arm in order:
            p, r = cells[arm][i]
            out.append({"run_id": f"A2-claude-{arm}-{p}-r{r}", "study": "A2", "agent": "claude",
                        "arm": arm, "prompt_id": p, "rep": r})
    return out
