# Test audit — sdispater/tomlkit — 2026-09-15

[tomlkit](https://github.com/sdispater/tomlkit) is a style-preserving TOML parser
(850 ★, used by Poetry). Audited at commit `4b38bec` (2026-09-11) with
`skills/falsifiable-tests/scripts/mutate.py`; the `toml-test` submodule was fetched so the
compliance suite runs. Fourteen suite runs, about ninety seconds.

## Scope
- Tests in suite: 1058 collected (378 hand-written + 680 generated from the
  [toml-test](https://github.com/toml-lang/toml-test) compliance corpus), 0 skipped
- Examined: **12 targeted mutations** in `_utils.py`, `items.py`, `parser.py` and
  `api.py` — number and string parsing, datetime offsets, `unwrap()` on each scalar,
  comment preservation, `sort_keys`. Chosen from what a parser most needs to get right
  plus the grep suspects (eleven tests with no assertion of their own, all delegating to
  a helper). The 899 tests no mutation reached are **not examined**.
- Suite state at audit time: green

## Summary

| Verdict | Count |
|---|---|
| Verified | 159 of 1058 |
| Vacuous (with respect to the value they name) | 2, plus 8 siblings with the same shape |
| Coverage gaps (mutations nothing caught) | 1 |
| Structural finding | the compliance suite uses the subject as its own oracle for datetimes |
| Not examined | 899 |

Comment preservation — the library's reason to exist — is guarded hard: dropping
comments from output reddened 87 tests, and failing to capture them in the parser 95.
Sign handling, escape sequences and `unwrap()` types are all caught.

## Findings

### Vacuous — `unwrap()` tests check the type, never the value

| Test | Claim | Mutation applied | Result |
|---|---|---|---|
| `tests/test_items.py::test_true_unwrap` | `item(True).unwrap()` is `True` | `Bool.unwrap` returns `not bool(self)` | still passed |
| `tests/test_items.py::test_false_unwrap` | `item(False).unwrap()` is `False` | same | still passed |

Both go through `elementary_test(v, type)` in `tests/util.py`, which asserts
`isinstance(v.unwrap(), type)` and that the result is not a tomlkit type — and nothing
else. A `Bool` that unwraps to the wrong boolean is still a `bool`. The same helper
backs `test_integer_unwrap`, `test_float_unwrap`, `test_string_unwrap`,
`test_datetime_unwrap`, `test_date_unwrap`, `test_time_unwrap` and `test_null_unwrap`;
those went red under the type-changing mutations (`Integer.unwrap` → `str`: 46 tests
red), so they do detect the wrong *type*, but by construction none of them can detect
the wrong *value*. `666` unwrapping to `667` would pass every one.

### Coverage gap

| Mutation | Checked for equivalence | What it means |
|---|---|---|
| RFC 3339 offset minutes ignored (`+05:30` parsed as `+05:00`) | No input anywhere in `tests/` — hand-written or compliance corpus — carries a non-zero minute offset, so for the suite's inputs the mutant is equivalent. Real inputs (`+05:30`, `+05:45`, `-03:30`) would be wrong by 30–45 minutes. | Half-hour timezones are unguarded. |

### Structural — the compliance suite cannot see datetime bugs

`tests/test_toml_tests.py` builds the expected value for every datetime case with
`tomlkit._utils.parse_rfc3339` — the function under test. When the negative-offset sign
was dropped, the parser and the expectation drifted together:

| Mutation | Compliance tests red (of 680) | Hand-written tests red (of 378) |
|---|---|---|
| tz offset sign ignored | **0** | 3 |
| integer sign dropped | 6 | 1 |
| string escapes not translated | 7 | 3 |

For integers and strings the corpus is an independent oracle (`int`, `str`). For all
four datetime types it is not: the 680 compliance cases would stay green under any
`parse_rfc3339` bug whatsoever, and the whole guard is three hand-written tests in
`test_utils.py` and `test_items.py`. This is the "expected value computed by the
subject" pattern from `references/vacuous-patterns.md`, and it hides in a suite that
looks like the strongest kind — an external conformance corpus.

### Verified (examples; per-test matrix in `tomlkit-matrix.json`)

- `test_original_string_and_dumped_string_are_equal[*]` and 80+ others — red when
  comments are dropped from output or not captured by the parser
- `test_parse_rfc3339_datetime[…-07:00-…]` ×2, `test_datetimes_behave_like_datetimes` —
  red when the negative offset sign is ignored (the only three that are)
- `test_booleans_comparison` — red when `Bool.__bool__` is inverted; the one test that
  reads `assert boolean` on sight as truthiness-only, and turns out to be exactly right
  for a `Bool` wrapper
- `test_dumps_sort_keys` (1 test) — red when `sort_keys` is ignored. Thin but real.
- 46 tests red when `Integer.unwrap` returns a string, 10 when the float sign is
  dropped, 10 when escape sequences are left untranslated

## Recommended fixes

1. `elementary_test`: take the expected value as well as the type —
   `elementary_test(item(False), bool, False)` — and assert `v.unwrap() == expected`.
   One helper change repairs nine tests.
2. `test_toml_tests.py`: build datetime expectations with an independent parser
   (`datetime.fromisoformat` handles RFC 3339 from Python 3.11) so the corpus can catch
   what it currently cannot.
3. Add a `+05:30`-style offset to `test_parse_rfc3339_datetime`'s parameters.

## Reproduce

```bash
git clone https://github.com/sdispater/tomlkit && cd tomlkit && git checkout 4b38bec
git submodule update --init
python3 -m venv .venv && .venv/bin/pip install -e . pytest pyyaml
cp <this repo>/case-studies/tomlkit-mutations.json mutations.json
.venv/bin/python <this repo>/skills/falsifiable-tests/scripts/mutate.py --project . \
  --spec mutations.json --junit report.xml \
  --test-cmd ".venv/bin/python -m pytest -q -p no:cacheprovider --junit-xml=report.xml"
```
