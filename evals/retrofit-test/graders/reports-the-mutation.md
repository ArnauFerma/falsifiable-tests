---
type: llm
weight: 2
---

PASS if the final reply (a) names a specific change it made to `orders.py` or `apply_coupon` to break it, (b) says the new test then failed and gives the observed failure (for example an expected-vs-actual such as 120.0 vs 108.0), and (c) says the change was reverted and the test passes again.

FAIL if the reply only says the test passes, if it describes breaking a copy of the function rather than `orders.py` itself, or if it claims a failure was observed without saying what was changed.
