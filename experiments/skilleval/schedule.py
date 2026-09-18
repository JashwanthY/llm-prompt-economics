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
