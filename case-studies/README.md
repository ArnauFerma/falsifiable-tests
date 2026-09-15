# Case studies

The method applied to open-source projects nobody involved with this skill wrote, using
the bundled harness, on the day stated in each report. Every verdict carries the mutation
that produced it, so you can disagree with a line rather than with the report.

| Project | Suite | Examined | What turned up |
|---|---|---|---|
| [tenacity](tenacity.md) | 184 tests | 12 mutations | 3 repr tests that cannot fail, 2 decorative tests, an unguarded backoff cap, a statistic asserted with `mock.ANY` everywhere |
| [tomlkit](tomlkit.md) | 1058 tests | 12 mutations | 9 `unwrap()` tests that check the type but never the value; the 680-case compliance corpus uses the subject as its own oracle for datetimes, so it cannot see datetime bugs |
| [click](click.md) | 2084 tests (31,000 stress tests deselected by default) | 10 mutations | 0 vacuous tests; a non-strict xfail; the documented "first non-empty envvar" rule has no test; the grep triage produced only false positives |

Each report follows `references/audit.md`: scope stated first, sample stated honestly,
verdicts with evidence, fixes proposed but not applied. The `*-mutations.json` beside each
report is the exact spec that was run; the reproduce block at the bottom of each report
re-runs it.

## What these are not

They are not audits of the whole suite. Each examines the tests that a dozen targeted
mutations reach — the conditions a library most needs to get right — and says nothing
about the rest. A test listed as "not examined" is not suspected of anything.

They are also not bug reports against the projects. Every finding is about what the test
suite can and cannot detect, not about the code being wrong; in every case the code was
correct. Where a fix seemed worth the maintainers' time it has been offered upstream, and
the report says so.

## Contributing one

Pick a project, follow `references/audit.md`, run the harness, write the report from the
template. Two rules: state the sample, and never list a test as verified without having
seen it red. Reports on suites where the method found *nothing* are as welcome as the
others — "twelve mutations, twelve caught, no findings" is a real result.
