# Exercise — Pick the status code

**Format:** apply · **Unit:** 01 · **Rests on:** Methods and status codes › Status codes

An orders API receives these four requests. For each one, give the status code the response should carry and one sentence on why, naming who caused the outcome: client or server.

1. `GET /orders/42`, and order 42 was never created.
2. `POST /orders` with a valid body; the order is created.
3. `GET /orders` while the database is down for maintenance.
4. `GET /orders/42` for an order that moved to `/archive/orders/42` for good.

**Submit:** a `.md` with four lines, one per request.
