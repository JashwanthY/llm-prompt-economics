from schedule import make_schedule


def test_every_cell_exactly_once():
    s = make_schedule()
    assert len(s) == 48 and len({r["run_id"] for r in s}) == 48
    assert {(r["agent"], r["arm"], r["prompt_id"], r["rep"]) for r in s} == {
        (a, arm, p, rep) for a in ("claude", "codex") for arm in ("off", "on")
        for p in ("P1", "P2", "P3", "P4") for rep in (1, 2, 3)}


def test_arms_strictly_alternate_within_each_agent():
    for agent in ("claude", "codex"):
        arms = [r["arm"] for r in make_schedule() if r["agent"] == agent]
        assert all(a != b for a, b in zip(arms, arms[1:]))


def test_agents_interleave_and_the_seed_fixes_the_order():
    s = make_schedule()
    assert [r["agent"] for r in s[:4]] == ["claude", "codex", "claude", "codex"]
    assert s == make_schedule() and s != make_schedule(seed=18)


def test_a2_every_cell_once_in_triplets_of_one_arm_each():
    from schedule import make_schedule_a2
    s = make_schedule_a2()
    assert len(s) == 36 and len({r["run_id"] for r in s}) == 36
    assert {(r["arm"], r["prompt_id"], r["rep"]) for r in s} == {
        (arm, p, rep) for arm in ("off", "on", "instr") for p in ("P1", "P2", "P3", "P4") for rep in (1, 2, 3)}
    assert all(r["agent"] == "claude" and r["study"] == "A2" and r["run_id"].startswith("A2-claude-") for r in s)
    for i in range(0, 36, 3):
        assert sorted(r["arm"] for r in s[i:i + 3]) == ["instr", "off", "on"]
    assert s == make_schedule_a2() and s != make_schedule_a2(seed=19)
