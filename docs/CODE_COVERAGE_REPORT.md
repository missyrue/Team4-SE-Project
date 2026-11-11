# Code Coverage Report

Date of run: 2026-11-11  
Tool: coverage.py through pytest-cov, `--cov=app`.

## Summary

| Statements | Missed | Line coverage |
|---|---|---|
| 774 | 28 | 96.4% |

Line coverage = the share of program lines that ran at least once during the tests.

## Per file

| File | Statements | Missed | Covered | Missed line numbers |
|---|---|---|---|---|
| app\audit.py | 4 | 0 | 100.0% | - |
| app\config.py | 4 | 0 | 100.0% | - |
| app\database.py | 14 | 4 | 71.4% | 20, 21, 22, 24 |
| app\main.py | 28 | 2 | 92.9% | 21, 22 |
| app\models.py | 85 | 0 | 100.0% | - |
| app\passwords.py | 17 | 0 | 100.0% | - |
| app\routers\admin.py | 195 | 10 | 94.9% | 133, 134, 135, 136, 137, 162, 190, 195, 196, 197 |
| app\routers\auth.py | 67 | 1 | 98.5% | 57 |
| app\routers\cart.py | 76 | 4 | 94.7% | 34, 35, 36, 99 |
| app\routers\catalogue.py | 51 | 0 | 100.0% | - |
| app\routers\mock_gateway.py | 16 | 1 | 93.8% | 31 |
| app\routers\orders.py | 114 | 3 | 97.4% | 44, 97, 99 |
| app\security.py | 28 | 1 | 96.4% | 39 |
| app\services\inventory.py | 55 | 2 | 96.4% | 79, 80 |
| app\services\payment.py | 8 | 0 | 100.0% | - |
| app\services\pricing.py | 12 | 0 | 100.0% | - |

## Reading the gaps

Missed lines are mostly defensive error paths (for example a database error branch) and the audit log helper that is exercised through the admin features.