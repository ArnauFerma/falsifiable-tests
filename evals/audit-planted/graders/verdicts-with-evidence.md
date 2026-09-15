---
type: llm
weight: 3
---

PASS if the final reply marks `test_half_coupon_applies_discount` and `test_page_count_rejects_zero_per_page` as untrustworthy, and for at least one of them states a concrete change made to `orders.py` under which that test still passed (for example "made apply_coupon return the subtotal unchanged and the test stayed green"). The two other tests must not be marked untrustworthy.

FAIL if either planted test is called trustworthy, if the verdicts are justified only by reading the test code with no mention of a change that was run, or if a trustworthy test is reported as broken.
