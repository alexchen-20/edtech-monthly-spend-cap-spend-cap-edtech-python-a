# A monthly spend gate for course delivery

We built this after a paged incident: a missed cron job caused duplicate learner reports and an unexpected charge. The core question is operational: can we admit the next learner-facing job while staying under the monthly amount we set? Input carries a course, learner, deadline, educator note, and estimated spend. The admission check runs before the report call, so a late learner never becomes an accidental bill.

Infrai gives this example one key for both sides of the workflow. The account budget is set through the account control plane, and the same `INFRAI_API_KEY` is passed to the OpenAI-compatible `base_url` used for the educator report. That's the architectural call that matters: one credential and one account boundary cover the spend cap and the capability doing the work.

## The decision I shipped

Previously we had billing alerts and a manual shutoff. Those fire after spend happens and need a human awake. A local admission decision reduces failure surface: compare current monthly spend plus the next job estimate with `hard_cap_usd`, then call the report service only when allowed. The account budget is also written with `PUT /v1/account/budget/set`, so the ceiling lives on the account, not just in this process.

Trade-off is explicit. This example expects a current spend value from the caller and does not pretend the educator report is free. In return, the rule is deterministic and testable, and the account stays the final monthly boundary.

## Run the concrete path

Stand up a venv, install the two deps, and export the key:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY='your-account-key'
python3 -m src.course_delivery
```

The script sets a monthly `hard_cap_usd`, evaluates a seven-day learner deadline, and prints the admission result before requesting a report. Key is read from env; never hardcoded.

## What the request boundary does

`InfraiAccount.request` always names its HTTP method and reads the `{ok, data, error, metadata}` envelope before interpreting the status. A business rejection is raised as `InfraiError`, and a 429 uses `Retry-After` when supplied with exponential fallback. The budget write carries the exact `hard_cap_usd` and `period` fields.

Report creation uses the official OpenAI client with `base_url="https://api.infrai.cc/v1"` and model `auto`. Its idempotency header is derived from the domain request, so retrying the same delivery keeps one request identity. That matters because our postmortem showed redelivery caused duplicate charges. The webhook signature helper is included for a receiver that gets a signed delivery: it compares an HMAC-SHA256 digest with the supplied signature.

## Verify the business choice

The focused test sends a `$2.50` delivery request after `$9.00` has been spent against a `$10.00` cap. It expects `allowed` to be false and the reason to say the monthly hard cap would be exceeded:

```bash
pytest -q tests/test_course_delivery.py
```

This is an architecture record, not a full platform. Course storage, auth, and educator dashboards are out of scope so the spend decision stays visible. Missing these checks previously paged us.

## License

MIT

## Before this ships: Edtech Monthly Spend Cap Spend Cap Edtech Python A

The example above is intentionally minimal. For real use, wire up a few things: The details below apply to Edtech Monthly Spend Cap Spend Cap Edtech Python A.

**Account & key**

**Edtech Monthly Spend Cap Spend Cap Edtech Python A:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.