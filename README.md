# falsifiable-tests

A Claude Code skill. A test that has never been seen to fail is not evidence — it is a
claim about the code that has itself never been tested.

The skill makes the agent prove a test can fail before treating it as verification:
break the code under test, confirm the test turns red *for the right reason*, restore.

## Install

As a plugin (recommended — updates with `/plugin update`):

```
/plugin marketplace add ArnauFerma/falsifiable-tests
/plugin install falsifiable-tests@falsifiable-tests
```

Or clone it straight into your personal skills directory:

```bash
git clone https://github.com/ArnauFerma/falsifiable-tests ~/.claude/skills/falsifiable-tests
```

Or into a single project:

```bash
git clone https://github.com/ArnauFerma/falsifiable-tests .claude/skills/falsifiable-tests
```

Either way it loads automatically when tests are written, modified or reviewed, and can
be invoked directly with `/falsifiable-tests` (or `/falsifiable-tests:falsifiable-tests`
when installed as a plugin).

## Contributing

Issues and pull requests are welcome, especially:

- a stack reference for a framework not yet covered (`references/`), following the shape
  of the existing ones: run exactly one test, read the failure correctly, stack-specific
  mutations, framework traps, flakiness checks, restoring
- results from running it on a real codebase, whether it found something or not — see
  "What was measured" below for why that matters
- vacuous-test patterns that are missing from `references/vacuous-patterns.md`

Changes to `scripts/mutate.py` need a test in `scripts/test_mutate.py`, and the test
needs its red proof — run the harness against itself with your change reverted as the
mutation and confirm the new test is what catches it.

## What it contains

```
.claude-plugin/             plugin and marketplace manifests
SKILL.md                    the method: the red proof, degenerate returns, honesty rules
references/php.md           PHPUnit and Pest
references/java.md          JUnit 4/5 with Maven or Gradle
references/javascript.md    Vitest, Jest, node:test
references/pytest.md        Python
references/other-stacks.md  Go, Rust, Ruby, Bats, HTTP and data tests
references/mutations.md     how to choose a mutation, and what to do when none works
references/vacuous-patterns.md  field guide to tests that cannot fail
references/audit.md         auditing an existing suite, with a report template
scripts/mutate.py           batch harness: many mutations, which tests noticed, safe restore
scripts/test_mutate.py      the harness's own tests (python3 -m pytest scripts/ -q)
```

`scripts/mutate.py` is language-agnostic. It edits the real file, runs your real test
command, restores from a hash-checked backup, re-runs the suite on the restored tree,
and reports which tests stayed green under every mutation (vacuity candidates), which
mutations no test caught (defects that could ship — or equivalent mutants), and which
mutations only broke the plumbing (errors, vanished tests: not counted as catches,
because a red for the wrong reason is not a proof). It sets `PYTHONDONTWRITEBYTECODE`
so a size-preserving mutation cannot leave a stale `.pyc` behind. Any suite that emits JUnit XML gets per-test resolution — PHPUnit via
`--log-junit`, Maven/Gradle via surefire reports, Vitest/Jest via a junit reporter,
pytest via `--junit-xml`.

## What was measured

Developed against a benchmark of small fixtures with deliberately vacuous tests planted
in them, run with and without the skill. Reported plainly because the skill asks the
same of its users:

| Configuration | Result |
|---|---|
| Claude Opus 5, with and without the skill | **No measurable difference.** Opus 5 performs the red proof unprompted, whether or not the prompt raises any suspicion about the tests. |
| Claude Haiku 4.5, first version | +12 points, but with a serious defect: in one task of four it *claimed* to have verified tests by mutation when it had not. |
| Claude Haiku 4.5, current version | 16/17 assertions against 11/17 for no skill. The false-verification failure mode did not recur. |

The fix that closed it was making the proof countable rather than exhorted: N mutations
require at least N+2 runs of the suite (baseline, one per mutation, one after the final
restore), and reimplementing a broken copy of a function is explicitly not a mutation,
because the tests never import it.

**Limitations.** One run per cell, no repeats, so individual point differences are
within sampling noise. The fixtures are small and Python-only. The skill's guidance on
budget and sampling for large suites has never been measured at all. The evaluation was
designed and graded by the same agent that wrote the skill; the code-correctness checks
were independent of the agents' own tests, but the judgement calls were not blind.

If you use it on a large real codebase and it finds nothing — or finds something — that
is more informative than the numbers above.

## Licence

Apache 2.0. See `LICENSE` and `NOTICE`.
