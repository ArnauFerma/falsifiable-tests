#!/bin/bash
set -e
# The scaffold runs outside the agent's sandbox, so it can reach PyPI; the agent cannot.
python3 -m venv .venv && .venv/bin/pip install -q pytest
cat > orders.py <<'PY'
COUPONS = {"TEN": 0.10, "HALF": 0.50}


def apply_coupon(subtotal, code):
    """Return the subtotal with the coupon's discount applied, rounded to cents."""
    return round(subtotal * (1 - COUPONS[code]), 2)


def page_count(items, per_page):
    """Number of pages needed to show `items` at `per_page` per page."""
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    return (items + per_page - 1) // per_page
PY
# plant the bug: floor division instead of ceiling
python3 - <<'PY'
p = "orders.py"
s = open(p).read().replace("return (items + per_page - 1) // per_page", "return items // per_page")
open(p, "w").write(s)
PY
mkdir -p tests
touch tests/__init__.py
cat > tests/test_orders.py <<'PY'
from orders import page_count


def test_page_count_rounds_up():
    assert page_count(11, 5) == 3


def test_page_count_exact_fit():
    assert page_count(10, 5) == 2
PY
printf '.venv/\n' > .gitignore
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture"
