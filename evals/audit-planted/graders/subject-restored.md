---
type: regex
target: { source: file, path: orders.py }
pattern: 'return round\(subtotal \* \(1 - COUPONS\[code\]\), 2\)'
weight: 3
---
