# Test audit — pallets/click — 2026-09-15

[click](https://github.com/pallets/click) is the Pallets command-line toolkit (17.7k ★).
Audited at commit `6aabf09` (2026-09-05) with
`skills/falsifiable-tests/scripts/mutate.py --timeout 120`. Twelve suite runs at about
twenty seconds each.

This is the large, mature suite of the three case studies, and it was chosen partly to
see whether the skill's sampling guidance holds up when exhausting the suite is not an
option.

## Scope
- Tests in suite: 33,084 collected, **31,000 deselected by default** (`addopts = "-m 'not
  stress'"` in `pyproject.toml`; high-iteration race-condition tests, documented as
  opt-in). Of the 2,084 that run: 2,059 passed, 24 skipped (Windows-only), 1 xfailed.
- Examined: **10 targeted mutations** in `types.py`, `core.py`, `utils.py` and
  `termui.py` — boolean and choice parsing, range clamping, path existence, exit codes,
  stderr routing, environment variables, help output, `confirm()`. The 1,854 tests no
  mutation reached are **not examined**.
- Suite state at audit time: green

## Summary

| Verdict | Count |
|---|---|
| Verified | 205 of 2,059 |
| Vacuous | 0 found |
| Not run (quietly) | 1 non-strict xfail |
| Coverage gaps (mutations nothing caught) | 1 |
| Not examined | 1,854 |

Click's suite is the strongest of the three. Every behavioural mutation was caught on an
assertion, most by many tests: omitting the help's Options section reddened 87, ignoring
a single `envvar` 73, `confirm()` treating "n" as yes 14, `echo(err=True)` going to stdout
12. The grep triage produced only false positives (below), which is itself a result.

## Findings

### Not run — `xfail` without `strict`

`tests/test_chain.py::test_group_chaining` is marked `@pytest.mark.xfail` and
`xfail_strict` is not set anywhere in the configuration. It reports `XFAIL` while the
behaviour is broken and would report `XPASS` — not a failure — the day it is fixed.
Nothing would tell anyone the test can be un-marked. `@pytest.mark.xfail(strict=True)`
costs one keyword.

### Coverage gap — multiple environment variables

| Mutation | Checked for equivalence | What it means |
|---|---|---|
| `envvar=[A, B]` returns the first *set* variable instead of the first *non-empty* one (`if rv:` → `if rv is not None:`) | Not equivalent: with `A=""` and `B="b"` the original yields `"b"`, the mutant `""`. No test in the suite passes a list or tuple to `envvar` at all — `grep -n "envvar=[\[(]" tests/` is empty. | The documented "first non-empty value" rule (`core.py:2251`, `2711`) has no test. It could be inverted and the suite would stay green. |

### Thin

`Context.exit(code)` always exiting 0 was caught by exactly two tests
(`test_context::test_exit_not_standalone`, `test_testing::test_exit_code_and_output_from_sys_exit`).
Most exit-code assertions in the suite reach the code through `UsageError` and `Abort`,
which do not go through `Context.exit`. Two real reds, so verified — but thin for the
call that every `sys.exit`-style program termination goes through.

### Grep suspects that were not findings

The pattern grep flagged five "tests with no assertion":
`test_testing.py::test_python_input`, `test_prompt`, `test_hidden_prompt`,
`test_multiple_prompts` and two `test_callback`s. All are **inner functions** — `click`
commands defined *inside* a test and named `test_*` — which the real test then invokes
and asserts on (`assert result.output == "Foo: bar bar\nfoo=bar bar\n"`). pytest never
collects them. A reminder that the triage list is a list of things to look at, not a
list of findings; `references/vacuous-patterns.md` says so and this is what it looks
like in practice.

The 87 `assert result.exit_code == 0` lines the grep found are likewise not truthiness
checks in disguise: nearly every one is followed by an assertion on `result.output`.

### Verified (examples; per-test matrix in `click-matrix.json.gz`)

- `test_formatting::*`, `test_options::*help*` and 80 others — red when the Options
  section is omitted from `--help`
- 73 tests red when a single `envvar` is never read
- `test_termui::test_confirm*` and 12 others — red when `confirm()` answers yes to "n"
- 12 tests red when `echo(err=True)` writes to stdout
- `test_types::test_path_exists*` and 6 others — red when `Path(exists=True)` stops
  checking
- `test_types::test_int_range_clamp*` (3) — red when the lower clamp is skipped
- `test_choice*` (5) — red when `case_sensitive=False` is ignored
- `BOOL` parsing (3) — red when `"y"` maps to `False`

## Recommended fixes

1. `test_chain.py:221`: `@pytest.mark.xfail(strict=True)`, or set `xfail_strict = true`
   in `[tool.pytest.ini_options]` for the whole suite.
2. Add a test for `envvar=["A", "B"]` with `A` set to the empty string, asserting `B`'s
   value is used.
3. Optionally, one more direct `ctx.exit(n)` test with a non-zero `n` reached through a
   command body.

## On sampling a 2,000-test suite

Ten mutations reached 205 tests and took four minutes of machine time. Doubling the
mutation count would roughly double both. The skill's guidance — critical paths first,
then grep suspects, then say plainly what was not examined — produced a report that says
something definite about the parts of click that decide what a program does, and nothing
at all about the rest. That is the intended shape.

The one operational lesson came from a mutation that is *not* in the spec above: the
first attempt broke `confirm()`'s "yes" path with `default=None`, which turns its
"repeat until answered" loop into an infinite one, and the audit stalled for twenty
minutes. The harness gained `--timeout` that afternoon. Mutations must be survivable, and
"survivable" includes "terminates".

## Upstream

The two test changes are offered as [pallets/click#3870](https://github.com/pallets/click/pull/3870).

## Reproduce

```bash
git clone https://github.com/pallets/click && cd click && git checkout 6aabf09
python3 -m venv .venv && .venv/bin/pip install -e . pytest
cp <this repo>/case-studies/click-mutations.json mutations.json
.venv/bin/python <this repo>/skills/falsifiable-tests/scripts/mutate.py --project . \
  --spec mutations.json --junit report.xml --timeout 120 \
  --test-cmd ".venv/bin/python -m pytest -q -p no:cacheprovider --junit-xml=report.xml"
```
