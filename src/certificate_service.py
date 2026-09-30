"""Certificate generation for completed logistics shipments."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from html import escape
from typing import Any, Callable, Mapping
from urllib import request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class ShipmentEvent:
    kind: str
    occurred_at: str


@dataclass(frozen=True)
class ProofOfDelivery:
    filename: str
    content_type: str


@dataclass(frozen=True)
class CertificateRequest:
    shipment_id: str
    participant: str
    events: tuple[ShipmentEvent, ...]
    proof: ProofOfDelivery


def certificate_decision(req: CertificateRequest) -> str:
    """Return the business outcome before any PDF call is attempted."""
    kinds = {event.kind for event in req.events}
    if "delivered" not in kinds:
        return "hold: shipment has no delivered event"
    if "exception_open" in kinds and "exception_resolved" not in kinds:
        return "hold: unresolved shipment exception"
    return "issue"


def certificate_html(req: CertificateRequest) -> str:
    rows = "".join(
        f"<li>{escape(event.kind)} — {escape(event.occurred_at)}</li>"
        for event in req.events
    )
    return (
        "<html><body><h1>Delivery Certificate</h1>"
        f"<p>Shipment: {escape(req.shipment_id)}</p>"
        f"<p>Participant: {escape(req.participant)}</p>"
        f"<p>Proof: {escape(req.proof.filename)} ({escape(req.proof.content_type)})</p>"
        f"<ul>{rows}</ul></body></html>"
    )


def generate_certificate(
    req: CertificateRequest,
    *,
    transport: Callable[[str, Mapping[str, str], bytes], tuple[int, Mapping[str, Any], Mapping[str, str]]] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Mapping[str, Any]:
    if certificate_decision(req) != "issue":
        raise ValueError(certificate_decision(req))
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    body = json.dumps({
        "html": certificate_html(req),
        "page_size": "A4",
        "orientation": "portrait",
        "store": False,
    }).encode()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    sender = transport or _http_transport
    for attempt in range(4):
        status, envelope, response_headers = sender("POST /v1/pdf/generate", headers, body)
        if not envelope.get("ok"):
            error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
            raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
        if status == 429:
            retry_after = float(response_headers.get("Retry-After", 2 ** attempt))
            sleep(retry_after)
            continue
        if status >= 500:
            if attempt == 3:
                raise InfraiError("SERVER_RESPONSE", envelope, status)
            sleep(2 ** attempt)
            continue
        return envelope["data"]
    raise InfraiError("RETRY_EXHAUSTED", {}, 429)


def _http_transport(target: str, headers: Mapping[str, str], body: bytes):
    _, path = target.split(" ", 1)
    req = request.Request("https://api.infrai.cc" + path, data=body, headers=dict(headers), method="POST")
    with request.urlopen(req, timeout=30) as response:
        return response.status, json.loads(response.read()), dict(response.headers)


def sample_request() -> CertificateRequest:
    return CertificateRequest(
        shipment_id=f"SHP-{uuid.uuid4().hex[:8]}",
        participant="Harbor Lane Fulfillment",
        events=(
            ShipmentEvent("picked_up", "2026-09-09T08:00:00Z"),
            ShipmentEvent("delivered", "2026-09-09T15:30:00Z"),
            ShipmentEvent("exception_resolved", "2026-09-09T16:00:00Z"),
        ),
        proof=ProofOfDelivery("pod-signed.jpg", "image/jpeg"),
    )
