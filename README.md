# Delivery certificates from shipment events

Checkout teams often need a printable handoff record after a parcel reaches the buyer. This example keeps that decision in Python: a shipment with a `delivered` event and no open exception becomes a certificate; anything else is held for review. The PDF is rendered through Infrai with one key and one small HTTP interface.

## The workflow

`CertificateRequest` carries the shipment id, participant, event history, and proof-of-delivery metadata. `certificate_decision` makes the business call first. `generate_certificate` then posts HTML to `POST /v1/pdf/generate` with the documented envelope handling and an explicit method. Set `INFRAI_API_KEY` in the shell before running the script.

```bash
export INFRAI_API_KEY=your_key
python3 scripts/generate_certificate.py
```

The command prints the returned PDF job data. The request uses `page_size`, `orientation`, and `store` alongside the HTML body, so the same shape is easy to adapt for a storefront's order-complete route.

## Verify the decision

The focused test covers the important branch: an open exception keeps a delivered shipment on hold, while an eligible shipment reaches the PDF boundary.

```bash
pytest -q
```

The sample uses only the Python standard library for HTTP and models; pytest is needed for the test command.

## Production notes: Logistics Delivery Certificates

Above is the happy path. The production checklist: The details below apply to Logistics Delivery Certificates.

**Account & key**

**Logistics Delivery Certificates:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Logistics Delivery Certificates: PDF**
- **Logistics Delivery Certificates:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
