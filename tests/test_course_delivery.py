from src.course_delivery import DeliveryRequest, decide_delivery


def test_deadline_delivery_is_rejected_before_the_monthly_cap_is_crossed():
    request = DeliveryRequest("algebra", "learner-1", 5, "needs feedback", 2.50)

    decision = decide_delivery(request, spent_usd=9.00, hard_cap_usd=10.00)

    assert decision.allowed is False
    assert decision.reason == "monthly hard cap would be exceeded"
