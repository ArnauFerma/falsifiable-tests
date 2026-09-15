# Changelog

## 1.2.0 — 2026-09-15

**Layout.** The skill now lives at `skills/falsifiable-tests/` (standard plugin layout).
Plugin installs are unaffected; a manual install is now a clone plus a symlink of that
directory — see the README.

**Harness (`scripts/mutate.py`).**
- Per-test outcomes are `pass / fail / error / skip / absent`. Only `fail` counts as a
  catch; a mutation that produces only errors or vanished tests is reported as "broke the
  plumbing", never as caught. Absent tests are never counted as green.
- A test command that fails to execute (exit 126/127, no JUnit file) is reported as "did
  not run", with output, instead of as a red suite. Red baselines print output too.
- `--timeout SECONDS` bounds each run and kills the whole process group; a timed-out
  mutation is reported as neither caught nor survived.
- Restores on SIGTERM as well as Ctrl-C, and takes the in-flight suite down with it.
- `PYTHONDONTWRITEBYTECODE=1` for every run; a final green run against the restored tree
  (`--skip-final-run` to opt out).
- 21 tests in `scripts/test_mutate.py`, verified red by running the harness against its
  own source with 13 planted defects (`scripts/self-mutations.json`); CI gates on it.

**Method (`SKILL.md`, references).**
- What to do when asked to "make the tests pass": the fix goes in the subject, and a
  changed assertion is a new test that needs its own red.
- Test-first: stub the subject so the first red is on the assertion, not an ImportError.
- Equivalent mutants named and explained; a survived mutation is not a verdict.
- Step 1 now requires confirming the test ran; the run-count rule is N+2.

**Evidence.**
- `case-studies/`: the method applied to tenacity, tomlkit and click, with the mutation
  spec and per-test matrix for each, and the findings offered upstream.
- `evals/`: four cases for `claude plugin eval`, one per failure mode the skill targets.

**Packaging.** Plugin and marketplace manifests; MIT licence; the README says where the
method comes from (MCP-Bifrost's test suite) and scopes the benchmark's limitations to
the benchmark.

## 1.0.0 — 2026-09-14

Initial release: the four-step red proof, degenerate returns, honesty rules, stack
references for pytest / JS / Java / PHP / others, vacuous-pattern field guide, audit
procedure, and the batch harness.
