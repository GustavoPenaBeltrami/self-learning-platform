---
type: Concept
title: Idempotency
description: A request that leaves the server in the same state whether it is sent once or many times.
tags: [unit-01, methods]
depends_on: [/concepts/safe-method.md]
studied: [2026-09-22T1700, 2026-09-26T0930]
generated: { by: slp-session/example, at: 2026-09-26T10:10:00Z }
sources:
  - id: local-idem
    resource: ../../resources/idempotency.txt
    title: Idempotency, in one paragraph
---

# Definition

A method is idempotent when N identical requests leave the server in the same state as one.[^local-idem] GET, HEAD, PUT and DELETE are idempotent; POST and PATCH are not guaranteed to be.[^local-idem]

# Depends on

- [Safe method](/concepts/safe-method.md): every safe method is idempotent, but not the other way around.

# Examples

A client that retries a PUT after a timeout creates no duplicates; retrying a POST may create a second order. To retry a POST safely, the server accepts an idempotency key and replays the first result for it.[^local-idem]

# Common confusions

- Idempotent doesn't mean "same response": a second DELETE can return 404 and still be idempotent.
- Sending the same body doesn't make a POST idempotent.

[^local-idem]: Idempotency, in one paragraph
