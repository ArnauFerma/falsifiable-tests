#!/usr/bin/env python3
"""Batch red proof: apply mutations one at a time and record which tests notice.

Use this when auditing a suite, where proving tests one by one by hand is too slow.
For a single test you just wrote, the four-step proof in SKILL.md is faster than
setting this up.

The output is a matrix of test x mutation. What you are looking for is survivors:

  - a test that stays green under every mutation touching the behaviour it names
    is vacuous with respect to that behaviour
  - a mutation that no test notices is a coverage gap: that defect could ship

Language-agnostic. It only needs a shell command that runs your suite, and
optionally a JUnit XML report for per-test resolution (pytest --junit-xml=,
vitest/jest --reporters=junit, go-junit-report, gradle, and most others emit it).
Without JUnit XML it falls back to whole-suite pass/fail, which still finds
mutations nothing catches but cannot tell you which test did the catching.

USAGE

    python mutate.py --project . --spec mutations.json \
        --test-cmd "python -m pytest -q --junit-xml=report.xml" \
        --junit report.xml

    # whole-suite resolution only
    python mutate.py --project . --spec mutations.json --test-cmd "go test ./..."

SPEC FORMAT (mutations.json)

    [
      {
        "name": "apply_coupon ignores the discount",
        "file": "orders.py",
        "find": "return round(subtotal * (1 - COUPONS[code]), 2)",
        "replace": "return round(subtotal, 2)"
      }
    ]

`find` must appear exactly once in the file, so a mutation cannot land somewhere
you did not intend. Keep mutations small and survivable — a mutation that stops
the code importing tests only that the file is loaded, not that any assertion
discriminates.

SAFETY

Every targeted file is copied before the first mutation and restored after each
run, including on Ctrl-C or an unhandled error. The final act is a hash check of
every touched file; if any file does not match its original, the script says so
loudly and tells you where the backup is. Never leave a mutation in the tree.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Workspace:
    """Backs up every file a mutation touches and guarantees restoration."""

    def __init__(self, project: Path):
        self.project = project
        self.backup_dir = Path(tempfile.mkdtemp(prefix="mutate-backup-"))
        self.originals: dict[Path, str] = {}

    def protect(self, rel_path: str) -> Path:
        target = self.project / rel_path
        if not target.is_file():
            raise SystemExit(f"No such file to mutate: {target}")
        if target not in self.originals:
            backup = self.backup_dir / rel_path.replace("/", "__").replace("\\", "__")
            shutil.copy2(target, backup)
            self.originals[target] = sha256(target)
        return target

    def restore_all(self) -> None:
        for target in self.originals:
            rel = target.relative_to(self.project).as_posix()
            backup = self.backup_dir / rel.replace("/", "__")
            shutil.copy2(backup, target)

    def verify_clean(self) -> list[str]:
        """Return the files that do not match their original content."""
        return [
            str(target)
            for target, digest in self.originals.items()
            if sha256(target) != digest
        ]


def run_suite(test_cmd: str, project: Path, junit: Path | None):
    """Run the suite. Returns (suite_passed, {test_name: passed}).

    The per-test map is empty when no JUnit XML is available.
    """
    if junit and junit.exists():
        junit.unlink()

    result = subprocess.run(
        test_cmd, shell=True, cwd=project, capture_output=True, text=True
    )
    suite_passed = result.returncode == 0

    per_test: dict[str, bool] = {}
    if junit and junit.exists():
        try:
            root = ET.parse(junit).getroot()
        except ET.ParseError:
            return suite_passed, per_test
        for case in root.iter("testcase"):
            name = case.get("name") or "?"
            classname = case.get("classname") or ""
            key = f"{classname}::{name}" if classname else name
            failed = any(
                child.tag in ("failure", "error") for child in case
            )
            skipped = any(child.tag == "skipped" for child in case)
            if not skipped:
                per_test[key] = not failed
    return suite_passed, per_test


def validate_spec(mutations: list, project: Path) -> None:
    """Check every mutation lands before running any of them.

    Failing halfway through leaves you with a partial audit and a spec you have to
    debug anyway, so it is worth paying for the whole check up front. Escaping is
    the usual culprit: a `find` string written in JSON needs its backslashes
    doubled, and a mismatch here means the mutation would have silently done nothing.
    """
    problems = []
    for mutation in mutations:
        for key in ("name", "file", "find", "replace"):
            if key not in mutation:
                problems.append(f"{mutation.get('name', '<unnamed>')}: missing {key!r}")
        if problems:
            continue
        target = project / mutation["file"]
        if not target.is_file():
            problems.append(f"{mutation['name']}: no such file {target}")
            continue
        count = target.read_text(encoding="utf-8").count(mutation["find"])
        if count == 0:
            problems.append(
                f"{mutation['name']}: `find` text not present in {mutation['file']}. "
                f"Check escaping — in JSON a literal backslash must be written \\\\."
            )
        elif count > 1:
            problems.append(
                f"{mutation['name']}: `find` text appears {count} times in "
                f"{mutation['file']}; make it unique so the mutation lands where you meant."
            )
    if problems:
        print("Spec problems — nothing was mutated:")
        for problem in problems:
            print("  " + problem)
        raise SystemExit(1)


def apply_mutation(target: Path, find: str, replace: str, name: str) -> None:
    text = target.read_text(encoding="utf-8")
    target.write_text(text.replace(find, replace, 1), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--test-cmd", required=True)
    parser.add_argument("--junit", type=Path, default=None,
                        help="JUnit XML the test command writes; enables per-test resolution")
    parser.add_argument("--json-out", type=Path, default=None,
                        help="Write the full result matrix here")
    args = parser.parse_args()

    project = args.project.resolve()
    junit = (project / args.junit) if args.junit and not args.junit.is_absolute() else args.junit
    mutations = json.loads(args.spec.read_text(encoding="utf-8"))

    print("Baseline run (the suite must be green before mutating)...")
    baseline_passed, baseline_tests = run_suite(args.test_cmd, project, junit)
    if not baseline_passed:
        print("  Suite is RED before any mutation. Fix that first — every verdict")
        print("  below would be confounded by a failure you did not introduce.")
        return 1
    resolution = "per-test" if baseline_tests else "whole-suite"
    print(f"  green, {len(baseline_tests) or '?'} tests, {resolution} resolution\n")

    validate_spec(mutations, project)

    ws = Workspace(project)
    matrix: dict[str, dict[str, bool]] = {}
    unnoticed: list[str] = []

    try:
        for mutation in mutations:
            name = mutation["name"]
            target = ws.protect(mutation["file"])
            apply_mutation(target, mutation["find"], mutation["replace"], name)
            try:
                suite_passed, per_test = run_suite(args.test_cmd, project, junit)
            finally:
                ws.restore_all()

            matrix[name] = per_test
            if suite_passed:
                unnoticed.append(name)
            caught = sum(1 for ok in per_test.values() if not ok)
            status = "SURVIVED - no test noticed" if suite_passed else f"caught by {caught or 'the suite'}"
            print(f"  {name:<50} {status}")
    finally:
        ws.restore_all()
        dirty = ws.verify_clean()
        if dirty:
            print("\n!! RESTORATION FAILED for:")
            for path in dirty:
                print("   " + path)
            print(f"   Originals are in {ws.backup_dir} — restore them before doing anything else.")
            return 2

    print("\n" + "=" * 72)

    if baseline_tests:
        never_failed = [
            test for test in baseline_tests
            if all(matrix[m].get(test, True) for m in matrix)
        ]
        print(f"\nTests that stayed green under all {len(mutations)} mutations "
              f"({len(never_failed)}/{len(baseline_tests)}):")
        for test in sorted(never_failed):
            print("  " + test)
        print("\n  These are candidates, not verdicts. A test is only vacuous if it")
        print("  survives a mutation that violates the behaviour IT claims to check:")
        print("  read each one and decide whether any mutation above was aimed at it.")

    if unnoticed:
        print(f"\nMutations no test noticed ({len(unnoticed)}) - these defects could ship:")
        for name in unnoticed:
            print("  " + name)

    if args.json_out:
        args.json_out.write_text(
            json.dumps({"baseline_tests": baseline_tests, "matrix": matrix,
                        "unnoticed_mutations": unnoticed}, indent=2),
            encoding="utf-8",
        )
        print(f"\nMatrix written to {args.json_out}")

    print("\nAll mutated files restored and verified byte-identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
