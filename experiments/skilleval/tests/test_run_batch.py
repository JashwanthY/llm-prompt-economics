import json

from run_batch import is_finished


def _meta(root, run_id, n, status):
    d = root / "A" / run_id / f"a{n}"
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({"status": status}))


def test_finished_after_one_ok_or_two_errors(tmp_path):
    _meta(tmp_path, "r1", 1, "ok")
    assert is_finished("r1", root=tmp_path)
    _meta(tmp_path, "r2", 1, "error")
    assert not is_finished("r2", root=tmp_path)
    _meta(tmp_path, "r2", 2, "error")
    assert is_finished("r2", root=tmp_path)
    assert not is_finished("never-run", root=tmp_path)
