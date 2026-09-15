# Test audit — jd/tenacity — 2026-09-15

[tenacity](https://github.com/jd/tenacity) is a retry library (8.8k ★). Audited at
commit `3e58094` (2026-09-01) with `skills/falsifiable-tests/scripts/mutate.py`, on a
clean clone with `pytest` and `tornado` installed. Total harness time: about two minutes
for fourteen suite runs.

## Scope
- Tests in suite: 184 defined, 184 collected, 1 skipped (`trio` not installed)
- Examined: **12 targeted mutations** across `stop.py`, `wait.py`, `retry.py` and
  `__init__.py`, chosen as: the conditions that decide whether a retry happens at all
  (stop, wait, retry predicates, reraise, statistics, callbacks), plus every test the
  pattern grep flagged. Not a random sample of the rest — the 117 tests that no mutation
  reached are **not examined**, and nothing below says anything about them.
- Suite state at audit time: green

## Summary

| Verdict | Count |
|---|---|
| Verified (red on an assertion under a targeted mutation) | 66 of 183 |
| Vacuous | 3 |
| Decorative (cannot be falsified in place) | 2 |
| Coverage gaps (mutations nothing caught) | 3 |
| Flaky | not tested |
| Not examined | 117 |

The core is solid. Breaking the stop boundary reddened 28 tests, breaking the retry
predicate 36, `reraise=True` 8, the statistics counter 12, the `before_sleep` hook 5,
exponential backoff 7, and the `TryAgain` cause-unwrapping 3. All of those went red on
assertions, none on plumbing.

## Findings

### Vacuous

| Test | Claim | Mutation applied | Result |
|---|---|---|---|
| `tests/test_tenacity.py::TestBase::test_retrying_repr` | `repr(Retrying)` works | `BaseRetrying.__repr__` returns `""` | still passed — the test calls `repr()` and asserts nothing |
| `tests/test_asyncio.py::TestAsyncio::test_repr` | `repr(AsyncRetrying)` works | same | still passed |
| `tests/test_tornado.py::TestTornado::test_repr` | `repr(TornadoRetrying)` works | same | still passed |

These are smoke tests by design ("repr must not crash"), and they do catch a repr that
raises. They do not catch a repr that lies. Contrast `test_callstate_repr` two lines
below `test_retrying_repr`, which asserts on the string and is the shape these three
should have.

### Decorative — cannot be falsified

| Test | Why |
|---|---|
| `tests/test_tenacity.py::TestStopConditions::test_legacy_explicit_stop_type` | Body is `Retrying(stop="stop_after_attempt")` with a `type: ignore`. There is no string-handling code in `BaseRetrying.__init__` to mutate; the string is stored as-is. The test can only fail if the constructor starts raising on a string. Its name promises legacy support that the code does not have. |
| `tests/test_tenacity.py::TestWaitConditions::test_legacy_explicit_wait_type` | Same, with `wait="exponential_sleep"`. |

### Coverage gaps — mutations no test noticed

| Mutation | Checked for equivalence | What it means |
|---|---|---|
| `wait_incrementing` ignores `max` (`max(0, min(result, self.max))` → `max(0, result)`) | Not equivalent: with `max=3` the strategy returns `[1, 2, 3, 3, 3, 3]`, the mutant `[1, 2, 3, 4, 5, 6]`. The only test (`test_incrementing_sleep`) passes no `max`, so the cap path is never exercised. | The cap on incrementing backoff could be deleted and the suite would stay green. |
| `statistics["idle_for"]` never accumulated | Not equivalent: the value is wrong on every retry. Every assertion on statistics uses `"idle_for": mock.ANY` (four places). | The reported idle time could be permanently zero. |
| `BaseAction.__repr__` drops the class name | Not equivalent, but low-stakes: it is the debug repr of `RetryAction`/`DoSleep`, which nothing asserts on. | Cosmetic. Listed for completeness. |

### Thin

`stop_after_delay` boundary (`>=` → `>`) was caught by exactly one test
(`TestStopConditions::test_stop_after_delay`). That is a real red, so it is verified —
but one test is a thin guard for the boundary that decides whether a retry loop ends on
time.

### Verified (examples; 66 in total, per-test matrix in `tenacity-matrix.json.gz`)

- `test_stop_after_attempt` (three variants) — red under the `>=` → `>` boundary flip
- `test_retry_if_exception_of_type`, `test_context_manager_retry_one` and 34 others —
  red when `retry_if_exception_type` matches nothing
- `TestReraiseExceptions::*`, `TestContextManager::test_reraise` — red when
  `reraise=True` raises `RetryError` instead of the original
- `test_reraise_try_again_with_cause` — red under four different mutations, including
  the `TryAgain` cause-unwrapping one it exists for
- `test_before_sleep_log_returns_with_exc_info` — flagged by the grep as having no
  assertion of its own (it delegates), and went red when the `before_sleep` hook was
  never registered. A good example of why the grep produces suspects, not verdicts.

## Recommended fixes

1. `test_retrying_repr`, `test_repr` ×2: assert the string contains the class name and
   `stop=`/`wait=`, as `test_callstate_repr` already does.
2. `test_incrementing_sleep`: add a case with `max=` and an attempt number past the cap.
3. Statistics tests: pin `idle_for` to the sum of the sleeps the test controlled instead
   of `mock.ANY` (the wait is fixed in those tests, so the value is known).
4. `test_legacy_explicit_*_type`: either delete, or turn into the test the name promises
   (assert that a string is rejected, or that it is mapped to a strategy).

## Coverage gaps noticed while reading

None beyond the three above; the suite is broad. The 117 unexamined tests would need
their own mutations — the harness makes that a matter of adding to `mutations.json`.

## Upstream

Reported as [jd/tenacity#715](https://github.com/jd/tenacity/issues/715).

## Reproduce

```bash
git clone https://github.com/jd/tenacity && cd tenacity && git checkout 3e58094
python3 -m venv .venv && .venv/bin/pip install -e . pytest tornado
cp <this repo>/case-studies/tenacity-mutations.json mutations.json
.venv/bin/python <this repo>/skills/falsifiable-tests/scripts/mutate.py --project . \
  --spec mutations.json --junit report.xml \
  --test-cmd ".venv/bin/python -m pytest -q -p no:cacheprovider --junit-xml=report.xml"
```
