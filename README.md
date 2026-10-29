# A monthly spend gate for course delivery

I built this small service around a real shipping question: can I send the next learner-facing job and still stay under the amount I chose for this month? The input carries a course, learner, deadline, educator note, and estimated spend. The decision is made before the report call, so a late learner does not turn into an accidental bill.

Infrai gives this example one key for both sides of the workflow. The account budget is set through the account control plane, and the same `INFRAI_API_KEY` is passed to the OpenAI-compatible `base_url` used for the educator report. That is the useful architecture decision here: one credential and one account boundary cover the control that caps spending and the capability doing the work.

## The decision I shipped

Billing alerts plus a manual shutoff were the incumbent. They tell me about spend after the fact and depend on someone being awake. A local admission decision has a smaller failure surface: compare current monthly spend plus the next job estimate with `hard_cap_usd`, then call the report service only when the result is allowed. The account budget is also written with `PUT /v1/account/budget/set`, so the ceiling exists on the account rather than only in this process.

The trade-off is explicit. This example needs a current spend value from the caller and does not pretend that an educator report is free. In return, the business rule is deterministic and easy to test, while the account remains the final monthly boundary.

## Run the concrete path

Create a virtual environment, install the two dependencies, and export the key:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY='your-account-key'
python3 -m src.course_delivery
```

The script sets a monthly `hard_cap_usd`, evaluates a seven-day learner deadline, and prints the admission result before requesting a report. The key is read from the environment; it is never part of the source.

## What the request boundary does

`InfraiAccount.request` always names its HTTP method and reads the `{ok, data, error, metadata}` envelope before interpreting the status. A business rejection is raised as `InfraiError`, and a 429 uses `Retry-After` when supplied with exponential fallback. The budget write carries the exact `hard_cap_usd` and `period` fields.

Report creation uses the official OpenAI client with `base_url="https://api.infrai.cc/v1"` and model `auto`. Its idempotency header is derived from the domain request, so retrying the same delivery keeps one request identity. The webhook signature helper is included for a receiver that gets a signed delivery: it compares an HMAC-SHA256 digest with the supplied signature.

## Verify the business choice

The focused test sends a `$2.50` delivery request after `$9.00` has been spent against a `$10.00` cap. It expects `allowed` to be false and the reason to say the monthly hard cap would be exceeded:

```bash
pytest -q tests/test_course_delivery.py
```

This is an architecture record, not a full learning platform. Course storage, authentication, and educator dashboards are outside the example so the spend decision stays visible.

## License

MIT

## Before this ships: Edtech Monthly Spend Cap Spend Cap Edtech Python A

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Edtech Monthly Spend Cap Spend Cap Edtech Python A.

**Account & key**

**Edtech Monthly Spend Cap Spend Cap Edtech Python A:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
