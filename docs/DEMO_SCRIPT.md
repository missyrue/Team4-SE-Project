# Demo video scripts

## Sprint 1 cut (1 minute) - `docs/demo-sprint-1.mp4`

Start with `python -m scripts.seed` and `uvicorn app.main:app`. Show the browser at http://127.0.0.1:8000.

| Time | Show on screen | Say |
|---|---|---|
| 0:00 | GitHub: Project board (Sprint 1 items Done), Actions tab with green runs | "Backlog from the SRS, CI runs all tests on every push." |
| 0:10 | Register a new account, log in | "Registration and login, passwords stored as salted hashes (F-001..003)." |
| 0:20 | Catalogue: search "clean", filter a category, sort by price | "Search, filter, sort (F-004..007)." |
| 0:30 | Open a book detail, add it to the cart | "Book details and add to cart (F-008, F-009)." |
| 0:38 | Cart: change quantity to 99 -> stock message; remove an item | "Stock-aware cart (F-010, F-011)." |
| 0:48 | Terminal: `pytest` -> 69 passed | "69 unit and integration tests, including boundary and error cases." |
| 0:55 | GitHub: Pull requests tab (each member's PR) | "Every member's work went through reviewed pull requests." |

## Sprint 2 cut (2 minutes) - `docs/demo-sprint-2.mp4`

Record with any screen recorder (Windows: Win+G Game Bar, or OBS; Mac: Shift+Cmd+5; Zoom "record" also works).
Start with the server running and **fresh seed data**: `python -m scripts.seed` then `uvicorn app.main:app`.
Name the file `docs/demo-sprint-2.mp4` (and `docs/demo-sprint-1.mp4` for the 1-minute cut). If the file is over 25 MB,
upload it to Google Drive/YouTube (unlisted) and put the link in `docs/VIDEO_LINKS.md`.

| Time | Show on screen | Say |
|---|---|---|
| 0:00 | GitHub repo page: README, Actions tab with a green run, Project board | "Team 4 Online Bookstore. 38 backlog items from the SRS, CI runs all tests on every push." |
| 0:15 | Browser: catalogue, search "clean", filter category Technology, sort by price | "Customers can browse, search, filter and sort — OBS-F-004 to 008." |
| 0:30 | Register a new account, log in | "Registration and login; passwords are stored as salted hashes." |
| 0:40 | Open a book detail, add 2 to cart, change quantity to a value above stock → error message | "Stock-aware cart, OBS-F-011." |
| 0:55 | Checkout with bad address → error; good address → payment panel | "Validation, then the payment gateway." |
| 1:05 | Click **Simulate tampered result** → rejected; **Simulate failed payment** → cart kept; then **Pay successfully** → order number | "Only a correctly signed success marks the order paid, OBS-SR-006. Stock is reduced only now." |
| 1:20 | My orders → cancel one order | "Order history and cancellation." |
| 1:30 | Log out, log in as admin → Inventory tab → set a stock to 3 → "LOW STOCK" toast; Orders tab → mark as shipped | "Admin: inventory with low-stock alerts, order status." |
| 1:45 | Reports tab → sales report; Audit log tab | "Reports for a period and a full audit trail." |
| 1:55 | Terminal: `pytest` → all green; mention coverage | "167 automated unit and integration tests, 96% coverage." |
