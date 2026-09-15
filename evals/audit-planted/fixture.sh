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
mkdir -p tests
touch tests/__init__.py
cat > tests/test_orders.py <<'PY'
import pytest
from orders import apply_coupon, page_count


def test_ten_percent_coupon():
    assert apply_coupon(120.0, "TEN") == 108.0


def test_half_coupon_applies_discount():
    # planted: truthiness only — passes if the discount is never applied
    assert apply_coupon(80.0, "HALF")


def test_page_count_rounds_up():
    assert page_count(11, 5) == 3


def test_page_count_rejects_zero_per_page():
    # planted: name promises the rejection path, body tests the happy path
    assert page_count(10, 5) == 2
PY
printf '.venv/\n' > .gitignore
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture"
