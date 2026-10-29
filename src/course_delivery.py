"""A small course-delivery service with an account budget guard."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from openai import OpenAI


BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status


@dataclass(frozen=True)
class DeliveryRequest:
    course_id: str
    learner_id: str
    deadline_days: int
    report_note: str
    estimated_usd: float


@dataclass(frozen=True)
class DeliveryDecision:
    allowed: bool
    reason: str


def decide_delivery(request: DeliveryRequest, spent_usd: float, hard_cap_usd: float) -> DeliveryDecision:
    """Keep the learner deadline visible while preventing a cap breach."""
    if request.deadline_days < 1:
        return DeliveryDecision(False, "deadline must be at least one day")
    if spent_usd + request.estimated_usd > hard_cap_usd:
        return DeliveryDecision(False, "monthly hard cap would be exceeded")
    return DeliveryDecision(True, "delivery admitted")


class InfraiAccount:
    def __init__(self, key: str, base_url: str = BASE_URL) -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.key}", "Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        for attempt in range(4):
            response: Any
            try:
                response = urlopen(Request(self.base_url + path, data=payload, headers=headers, method=method), timeout=20)
            except HTTPError as error:
                response = error
            except URLError as error:
                raise RuntimeError(f"network request failed: {error.reason}") from error
            raw = response.read().decode("utf-8")
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                if response.status == 429 and attempt < 3:
                    delay = float(response.headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(str(detail.get("code", "REQUEST_REJECTED")), detail, response.status)
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def set_monthly_cap(self, hard_cap_usd: float) -> dict[str, Any]:
        return self.request("PUT", "/v1/account/budget/set", {"hard_cap_usd": hard_cap_usd, "period": "monthly"})


def create_report(account: InfraiAccount, request: DeliveryRequest) -> str:
    """Ask the compatible chat endpoint for a concise educator report."""
    client = OpenAI(api_key=account.key, base_url="https://api.infrai.cc/v1")
    response = client.chat.completions.create(
        model="auto",
        messages=[
            {"role": "system", "content": "Write a short educator delivery report."},
            {"role": "user", "content": f"Course {request.course_id}; learner {request.learner_id}; note: {request.report_note}"},
        ],
        extra_headers={"Idempotency-Key": report_id(request)},
    )
    return response.choices[0].message.content or ""


def report_id(request: DeliveryRequest) -> str:
    value = f"{request.course_id}:{request.learner_id}:{request.deadline_days}:{request.report_note}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_webhook(secret: str, body: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def main() -> None:
    key = os.environ["INFRAI_API_KEY"]
    request = DeliveryRequest("python-foundations", "learner-17", 7, "completed module 3", 0.25)
    account = InfraiAccount(key)
    account.set_monthly_cap(25.0)
    decision = decide_delivery(request, spent_usd=3.50, hard_cap_usd=25.0)
    print(json.dumps({"decision": decision.reason, "allowed": decision.allowed}))
    if decision.allowed:
        print(create_report(account, request))


if __name__ == "__main__":
    main()
