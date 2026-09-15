# Evals

Four cases for `claude plugin eval`, each aimed at one failure mode the skill exists to
prevent. Graders are mostly free checks over the transcript and the workspace; each case
has one LLM rubric.

| Case | Failure mode measured |
|---|---|
| `retrofit-test` | writing a test onto working code and calling it verified without ever seeing it red |
| `audit-planted` | marking planted vacuous tests as trustworthy, or justifying verdicts by reading instead of by a mutation that ran |
| `make-tests-pass` | making a red test green by editing the assertion, skipping it, or special-casing the subject |
| `no-tools-honesty` | fabricating a verification when nothing could be executed |

Three cases seed a workspace from a scaffold script and need Bash/Edit/Write; the fourth
deliberately has no tools. `claude plugin eval` only grants Bash inside its sandbox, so on
Linux the runs need `bubblewrap` and `socat` installed (`apt install bubblewrap socat`);
without them every shell case is refused with zero turns. `python3` must also be able to
import pytest — prepend a venv's `bin/` to `PATH` if the system interpreter cannot.

Run from the repository root:

```bash
claude plugin eval . --scaffold --allow-tools Bash Edit Write --trust-plugin
```

Add `--ablation none --runs 1` for a quick smoke pass. The default two-arm run reports the
score with and without the plugin and their difference; on models that already do the red
proof unprompted, expect a small Δ — the README's "What was measured" section says as much.

`results/` is gitignored. Each run also writes an HTML report there.
