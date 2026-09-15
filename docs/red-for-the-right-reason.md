# A test that has never failed is a claim, not evidence

*I broke a TOML parser's timezone handling on purpose. Its 680 official conformance tests stayed green. Here is why, and the habit that catches it.*

```
# tomlkit @ 4b38bec — parse_rfc3339, negative UTC offset sign dropped
#   before: if sign == "-": offset = -offset
#   after:  if False:       offset = -offset

tests/toml-test    ····································· 680 passed
tests/test_utils   ······································ 2 failed
tests/test_items   ······································ 1 failed
```

Three hand-written tests noticed. The conformance corpus did not.

tomlkit is the TOML library under Poetry. Its suite has 1,058 tests, and 680 of them are generated from [toml-test](https://github.com/toml-lang/toml-test), the language's official conformance corpus. It is the strongest kind of test suite a parser can have: an external oracle, hundreds of cases, maintained by someone else.

When I flipped the sign on negative UTC offsets so that `-07:00` parsed as `+07:00`, none of the 680 went red. The reason is one line in the test file: the expected value for every datetime case is built with `tomlkit._utils.parse_rfc3339` — the function under test. Parser and expectation drift together, and the suite cannot see any datetime bug at all. For integers and strings the corpus *is* independent (`int`, `str`), and it caught the same kind of break within seconds.

Nobody would find this by reading. The test file looks immaculate. You find it by breaking the code and watching what happens.

## Green means one of two things

Either the behaviour is correct, or the test cannot detect the behaviour being wrong. From the outside those are identical, and reading the test does not separate them — a vacuous test looks exactly like a real one, which is how it got written.

The only thing that separates them is observation:

1. Run the test against correct code. Green. Check the count line says it actually ran.
2. Break the code under test — the file the tests import, not a copy — in a way that violates exactly what the test claims.
3. Run again. It must fail **on the assertion**, with the expected-versus-actual you care about. An `ImportError` proves only that the file loads.
4. Restore, from git or a copy, never from memory. Green again.

A test counts as verification once it has been observed red for the right reason. Before that it is a claim about the code that has itself never been tested.

## Where this came from

I did not arrive at this from theory. I was building [MCP-Bifrost](https://github.com/ArnauFerma/MCP-Bifrost), an MCP server that hands mechanical code edits to a cheap worker model and validates them through a chain of gates. Two of the first fifteen tests were false greens: they printed their failures and never exited non-zero. Any exit-code-based runner would have counted them as passing forever.

After that, every test in the project got written this way — several hundred now, each seen red under a deliberate break before being trusted. The trouble was re-explaining the practice to Claude Code at the start of every session. So I packaged it as a skill: [falsifiable-tests](https://github.com/ArnauFerma/falsifiable-tests). Install it once and the agent does the proof whenever it writes, changes or reviews a test.

## What the skill actually changes

Most of it is the four steps above, plus the places where a proof quietly turns into a non-proof:

- **The shortcut that is not a proof.** Writing a broken *copy* of the function in a scratch file and checking it gives a different number. Your tests never ran against it. The suite imported the real module and stayed green throughout.
- **Counting.** Proving N mutations takes at least N+2 suite runs. Before saying "I verified these can fail", count the runs that actually happened. This one line is what stopped a smaller model from claiming verifications it had not run.
- **"Make the tests pass."** The fix goes in the subject. A changed assertion is a new test with no track record. Never special-case the test's input in the code.
- **Equivalent mutants.** A survived mutation is not automatically a vacuous test — `<` to `<=` changes nothing for `clamp(5, 5)`. Check the mutant actually changes the output for the test's input before blaming the test.
- **Honesty when it cannot run.** Read-only checkout, sandbox, missing tool: say "unverified", say which mutation you would have applied, and stop. Never ask for broader access to finish a proof.

Past one or two mutations you stop doing this by hand. The repo ships a harness that edits the real file, runs your real test command, restores from a hash-checked backup, and reports which tests noticed each mutation, which mutations nothing caught, and — separately — which mutations only broke the plumbing. It needs nothing from your stack beyond a shell command and, optionally, JUnit XML.

## Three suites nobody involved wrote

To see whether this finds anything outside my own code, I ran it against three open-source projects, a dozen targeted mutations each, on the conditions a library most needs to get right. Each report states its sample and says nothing about the tests it did not reach.

| Project | Tests | Mutations | What turned up |
|---|---:|---:|---|
| [tomlkit](https://github.com/ArnauFerma/falsifiable-tests/blob/main/case-studies/tomlkit.md) | 1,058 | 12 | The oracle problem above. Also nine `unwrap()` tests that check the type but never the value — `Bool.unwrap` returning the inverse passes `test_true_unwrap`. |
| [tenacity](https://github.com/ArnauFerma/falsifiable-tests/blob/main/case-studies/tenacity.md) | 184 | 12 | Three `repr` tests that call `repr()` and assert nothing; the cap on incrementing backoff can be deleted; `idle_for` is asserted with `mock.ANY` everywhere. The core — stop, wait, retry, reraise — reddened 28, 7, 36 and 8 tests respectively. |
| [click](https://github.com/ArnauFerma/falsifiable-tests/blob/main/case-studies/click.md) | 2,084 | 10 | Nothing vacuous. One non-strict `xfail`, one documented rule (first *non-empty* envvar of a list) with no test. Every grep "suspect" was a false positive. |

The click result matters as much as the tomlkit one. A method that only ever finds problems is a method you should not trust. Click's suite is excellent, and the report says so, with the mutations that prove it.

All three are reported upstream — an issue each for [tomlkit](https://github.com/python-poetry/tomlkit/issues/603) and [tenacity](https://github.com/jd/tenacity/issues/715), a small test PR for [click](https://github.com/pallets/click/pull/3870). None of it is a bug in their code; every finding is about what the suite can and cannot see.

## Does the skill change what the model does?

Measured with `claude plugin eval`, Claude Sonnet 5, three runs per case, with and without the plugin, on a fixture with a working `apply_coupon` and no tests:

| Prompt | With | Without | Δ |
|---|---:|---:|---:|
| "Add a pytest test for `apply_coupon`" | 1.00 ×3 | 0.40 ×3 | +0.60 |
| "`pytest` is failing. Make the tests pass." (real bug in the subject) | 1.00 ×3 | 1.00 ×3 | 0 |

Without the skill, Sonnet writes a correct value assertion and stops: no mutation, no observed red, and a reply that says the test passes. With it, all three runs did the full proof and named the change and the observed values. On the second prompt it fixes the subject rather than the assertion either way — that case has a ceiling and does not discriminate, and the write-up says so.

Earlier, on smaller planted-vacuous-test fixtures: Haiku 4.5 went from 11/17 to 16/17 and stopped claiming verifications it had not run; Opus-class models do the proof unprompted, with or without the skill. One run per cell there, graded by the same agent that wrote the skill. Every number above is in the repo with the case files, so anyone can re-run them.

## Install

```
/plugin marketplace add ArnauFerma/falsifiable-tests
/plugin install falsifiable-tests@falsifiable-tests
```

```
npx skills add ArnauFerma/falsifiable-tests   # Cursor, Codex, Copilot, Gemini CLI …
```

MIT. The skill text is agent-agnostic; the references cover pytest, Jest/Vitest, JUnit, PHPUnit and Go/Rust/Ruby/Bats. If you run it on a real suite and it finds nothing, that is a result too — I would like to hear about it as much as the other kind.

---

*The method is old — it is mutation testing with a small scope and a human reading the failure. What is new is that the agent writing the test is now the one most likely to write a vacuous one, and the one best placed to prove it isn't.*
