import pytest

from src.certificate_service import (
    CertificateRequest,
    ProofOfDelivery,
    ShipmentEvent,
    certificate_decision,
    generate_certificate,
)


def make_request(*kinds: str) -> CertificateRequest:
    return CertificateRequest("SHP-42", "Storefront buyer", tuple(ShipmentEvent(k, "today") for k in kinds), ProofOfDelivery("pod.pdf", "application/pdf"))


def test_unresolved_exception_holds_certificate():
    assert certificate_decision(make_request("delivered", "exception_open")) == "hold: unresolved shipment exception"


def test_generate_sends_only_after_issue(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    calls = []

    def transport(target, headers, body):
        calls.append((target, headers, body))
        return 200, {"ok": True, "data": {"job_id": "job-1"}}, {}

    result = generate_certificate(make_request("delivered"), transport=transport)
    assert result == {"job_id": "job-1"}
    assert calls[0][0] == "POST /v1/pdf/generate"
    assert "Bearer test-key" in calls[0][1]["Authorization"]


def test_hold_does_not_call_infrai(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    with pytest.raises(ValueError, match="no delivered"):
        generate_certificate(make_request("picked_up"), transport=lambda *_: (_ for _ in ()).throw(AssertionError()))
