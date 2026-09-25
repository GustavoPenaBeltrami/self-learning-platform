# Learning — Example topic: HTTP basics

## Mission

Design and review small REST APIs without guessing methods and codes: pick the right method for a request and justify it by safety and idempotency, and choose the status code a response should carry. Out of scope: HTTP/2 and caching headers.

## Glossary

**Idempotent**: a request that leaves the server in the same state whether it is sent once or many times. PUT and DELETE are; POST is not.
_Avoid_: repeatable, retry-safe

**Safe method**: a method that doesn't change server state. GET is safe; every safe method is idempotent.
_Avoid_: read-only

## Record

### 0002 — Mixed up 404 and 503 under load — corrected
Answered 404 for an overloaded server. Was reading the code by the symptom ("not found") instead of by who caused the failure. Corrected in the 2026-09-23 exam feedback. Check it again with 502 and 504.

### 0001 — Declared prior knowledge: GET and POST
Uses GET and POST daily in frontend code. Had never reasoned about idempotency. Level check: 3 questions, edge at PUT vs POST.
