# Branch Coverage Report

Date of run: 2026-11-11  
Tool: coverage.py with `--cov-branch`.

## Summary

| Branches | Covered | Missed | Branch coverage |
|---|---|---|---|
| 158 | 141 | 17 | 89.2% |

Branch coverage counts each side of every if/else and loop decision. A line can run while only one side of its decision was taken, so branch coverage is the stricter measure.

## Per file

| File | Branches | Covered | Missed | Branch coverage |
|---|---|---|---|---|
| app\audit.py | 0 | 0 | 0 | 100.0% |
| app\config.py | 0 | 0 | 0 | 100.0% |
| app\database.py | 0 | 0 | 0 | 100.0% |
| app\main.py | 2 | 2 | 0 | 100.0% |
| app\models.py | 0 | 0 | 0 | 100.0% |
| app\passwords.py | 2 | 2 | 0 | 100.0% |
| app\routers\admin.py | 34 | 30 | 4 | 88.2% |
| app\routers\auth.py | 12 | 10 | 2 | 83.3% |
| app\routers\cart.py | 16 | 14 | 2 | 87.5% |
| app\routers\catalogue.py | 16 | 16 | 0 | 100.0% |
| app\routers\mock_gateway.py | 4 | 3 | 1 | 75.0% |
| app\routers\orders.py | 34 | 30 | 4 | 88.2% |
| app\security.py | 8 | 7 | 1 | 87.5% |
| app\services\inventory.py | 28 | 25 | 3 | 89.3% |
| app\services\payment.py | 0 | 0 | 0 | 100.0% |
| app\services\pricing.py | 2 | 2 | 0 | 100.0% |