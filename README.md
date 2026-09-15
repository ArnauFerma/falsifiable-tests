# falsifiable-tests

[![CI](https://github.com/ArnauFerma/falsifiable-tests/actions/workflows/ci.yml/badge.svg)](https://github.com/ArnauFerma/falsifiable-tests/actions/workflows/ci.yml)

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

### Other agents

The skill text is agent-agnostic — it needs nothing from the host beyond "run a
test" and "show me the failure". The [skills.sh](https://skills.sh) CLI installs it
into Cursor, Codex CLI, GitHub Copilot, Gemini CLI, OpenCode, Windsurf and about
sixty others:

```bash
npx skills add ArnauFerma/falsifiable-tests                 # pick agents interactively
npx skills add ArnauFerma/falsifiable-tests -a cursor -a codex -a github-copilot -g
```

Or clone it anywhere and link the skill directory into your personal skills:

```bash
git clone https://github.com/ArnauFerma/falsifiable-tests
ln -s "$PWD/falsifiable-tests/skills/falsifiable-tests" ~/.claude/skills/falsifiable-tests
```

(or into a single project's `.claude/skills/`). `git pull` in the clone updates it.

In Claude Code it loads automatically when tests are written, modified or reviewed, and
can be invoked directly with `/falsifiable-tests` (or `/falsifiable-tests:falsifiable-tests`
when installed as a plugin). Other agents trigger on the frontmatter description the
same way.

## Contributing

Issues and pull requests are welcome, especially:

- a stack reference for a framework not yet covered (`references/`), following the shape
  of the existing ones: run exactly one test, read the failure correctly, stack-specific
  mutations, framework traps, flakiness checks, restoring
- results from running it on a real codebase, whether it found something or not — see
  "What was measured" below for why that matters
- vacuous-test patterns that are missing from `references/vacuous-patterns.md`

Changes to `scripts/mutate.py` need a test in `scripts/test_mutate.py` (both under
`skills/falsifiable-tests/`), and the test
needs its red proof — run the harness against itself with your change reverted as the
mutation and confirm the new test is what catches it.

## What it contains

```
.claude-plugin/                       plugin and marketplace manifests
skills/falsifiable-tests/
  SKILL.md                            the method: the red proof, degenerate returns, honesty rules
  references/php.md                   PHPUnit and Pest
  references/java.md                  JUnit 4/5 with Maven or Gradle
  references/javascript.md            Vitest, Jest, node:test
  references/pytest.md                Python
  references/other-stacks.md          Go, Rust, Ruby, Bats, HTTP and data tests
  references/mutations.md             how to choose a mutation, equivalent mutants, when none works
  references/vacuous-patterns.md      field guide to tests that cannot fail
  references/audit.md                 auditing an existing suite, with a report template
  scripts/mutate.py                   batch harness: many mutations, which tests noticed, safe restore
  scripts/test_mutate.py              the harness's own tests
  scripts/self-mutations.json         defects planted in the harness by CI; every one must be caught
evals/                                eval cases for `claude plugin eval` (see below)
```

`scripts/mutate.py` is language-agnostic. It edits the real file, runs your real test
command, restores from a hash-checked backup, re-runs the suite on the restored tree,
and reports which tests stayed green under every mutation (vacuity candidates), which
mutations no test caught (defects that could ship — or equivalent mutants), and which
mutations only broke the plumbing (errors, vanished tests: not counted as catches,
because a red for the wrong reason is not a proof). It sets `PYTHONDONTWRITEBYTECODE`
so a size-preserving mutation cannot leave a stale `.pyc` behind, bounds each run with
`--timeout` so a mutation that creates an infinite loop cannot stall the audit, and
restores on Ctrl-C and SIGTERM alike. Any suite that emits JUnit XML gets per-test resolution — PHPUnit via
`--log-junit`, Maven/Gradle via surefire reports, Vitest/Jest via a junit reporter,
pytest via `--junit-xml`.

## Where it comes from

The method predates the skill. It is how the tests in
[MCP-Bifrost](https://github.com/ArnauFerma/MCP-Bifrost) — an MCP server that
delegates code edits to a worker model and validates them through a chain of gates —
are written: several hundred tests, each one observed red under a deliberate break
before being trusted. The practice started after finding that two of the project's
first fifteen tests were false greens: they printed their failures and never exited
non-zero, so any exit-code-based runner would have counted them as passing forever
(the account is in Bifrost's
[critical review](https://github.com/ArnauFerma/MCP-Bifrost/blob/main/docs/critical-review.md)).

The skill exists so that practice can be installed instead of re-explained at the start
of every session.

## What was measured

The with-skill versus without-skill comparison below is a separate, smaller thing: it
asks whether the *skill text* changes what a model does, not whether the method works.
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

**Limitations of the benchmark.** One run per cell, no repeats, so individual point
differences are within sampling noise. The benchmark fixtures are small and Python-only.
The skill's guidance on budget and sampling for large suites has not been benchmarked,
although it is the guidance the Bifrost suite is maintained under. The evaluation was
designed and graded by the same agent that wrote the skill; the code-correctness checks
were independent of the agents' own tests, but the judgement calls were not blind.

If you use it on a large real codebase and it finds nothing — or finds something — that
is more informative than the numbers above.

## Licence

MIT. Use it, copy it, fold it into another skill — just keep the attribution line.
