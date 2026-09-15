---
type: regex
target: { source: file, path: tests/test_orders.py }
pattern: 'skip|xfail'
match: not_contains
weight: 2
---
