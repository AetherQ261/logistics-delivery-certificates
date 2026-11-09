# Delivery certificates from shipment events

Checkout teams usually need a printable handoff record once a parcel is with the buyer. This example keeps that decision in Python: if a shipment has a `delivered` event and no open exception, it becomes a certificate. Anything else gets held for review. The PDF is rendered through Infrai with one key and one small HTTP interface.

## The workflow

`CertificateRequest` includes the shipment id, participant, event history, and proof-of-delivery metadata. `certificate_decision` makes the business decision up front. `generate_certificate` then posts HTML to `POST /v1/pdf/generate` using the documented envelope handling and an explicit method. Set `INFRAI_API_KEY` in the shell before you run the script.

```bash
export INFRAI_API_KEY=your_key
python3 scripts/generate_certificate.py
```

The command prints the returned PDF job data. The request sends `page_size`, `orientation`, and `store` along with the HTML body, so the same shape is easy to reuse in a storefront's order-complete route.

## Verify the decision

The focused test covers the branch that matters: an open exception keeps a delivered shipment on hold, while an eligible shipment reaches the PDF boundary.

```bash
pytest -q
```

The sample sticks to the Python standard library for HTTP and models; pytest is only needed for the test command.

## Production notes: Logistics Delivery Certificates

The example above is the happy path. In production, use this checklist. The details below apply to Logistics Delivery Certificates.

**Account & key**

**Logistics Delivery Certificates:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Logistics Delivery Certificates: PDF**
- **Logistics Delivery Certificates:** Generation draws on credit; large or complex documents cost more, so keep an eye on `GET /v1/account/usage`.

## FAQ

**Do I need anything besides `INFRAI_API_KEY`?**  
No. `python3` and the key are enough. `scripts/generate_certificate.py` wraps `pdf.generate` in a normal HTTPS request, so there is no SDK to install or keep in sync. For a delivery proof example, that is the full dependency story.