import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tool():
    spec = importlib.util.spec_from_file_location("claims_tool", ROOT / "tools" / "claims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_headline_number_matches_its_results_file():
    errors = _tool().check()
    assert not errors, "\n".join(errors)


def test_a_wrong_number_is_caught(tmp_path):
    tool = _tool()
    ledger = tool.load()
    claim = next(c for c in ledger["claims"] if c.get("evidence"))
    name, ev = next(iter(claim["evidence"].items()))
    ev["value"] = (ev["value"] + 1) if isinstance(ev["value"], (int, float)) else "tampered"
    assert any(claim["id"] in e for e in tool.check_numbers(ledger))


def test_json_pointer_escapes():
    tool = _tool()
    assert tool.resolve({"a/b": {"c": [5, 6]}}, "/a~1b/c/1") == 6
