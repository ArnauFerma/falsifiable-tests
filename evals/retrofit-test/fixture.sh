#!/bin/bash
set -e
python3 -c "import pytest" 2>/dev/null || { echo "python3 cannot import pytest; install it (or prepend a venv to PATH) before running these evals" >&2; exit 1; }
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
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture"
