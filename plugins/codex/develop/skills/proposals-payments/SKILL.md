---
name: proposals-payments
description: "Manage Pai Console project SOW proposals and collections: compose/save/send proposals, record acceptance or rejection, link billing milestones, import income CFDI, record payment complements, and void payments. Use for proposals, quotations, SOWs, investment, invoices, CFDI, payment complements, received payments, collections, or voids."
argument-hint: "[project] [proposal, invoice, or payment]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Proposals and payments

Read shared `pai-console` first through the current client's skill mechanism. Most actions affect money or client commitments. Preserve Mexican Spanish business formatting, MXN amounts, and `America/Mexico_City` dates where required; reply in the user's language.

**Proposal transitions, CFDI imports, and payments cannot be undone** (except voiding a payment, also final). Before each, explain exactly what will be recorded and wait for explicit approval, including in staging.

Milestone collections use imported CFDI and recorded payments below. Stripe milestone checkout has been removed, including its endpoint, Console action, and IAM permission; it is not a disabled feature to re-enable.

## Proposals

In Console and Portal, staff find **Nueva propuesta** in the content toolbar above the proposal list. Client acceptance/rejection remains in Portal; this toolbar move does not change proposal permissions or transitions.

A proposal is a SOW: `pageContent` follows page type **`sow`**. All sections are required in this order. These Spanish section identifiers are contract values, not translatable prose:

| Section | Allowed blocks |
|---|---|
| `contexto` | text, callout |
| `alcance` | deliverables, text |
| `fuera-de-alcance` | text, cards |
| `plan` | timeline, steps, text |
| `inversion` | data-table, facts, text |
| `supuestos` | text, callout, risks |
| `fuentes` | sources |

Required somewhere: `deliverables`, `data-table`, `sources`. See `../resources/references/page-types.md`.

1. **Read** `proposal_list`, then `proposal_get` for an existing proposal. Projects retain proposal history; edit the current draft rather than duplicating it.
2. **Compose SOW:** deliverables with acceptance criteria, explicit exclusions (`fuera-de-alcance`) to prevent disputes, sourced investment `data-table`, assumptions. Validate with `page_validate {content, typeSlug:"sow"}`.
3. **Save:** `proposal_save {organizationId, projectId, createNew:true, title, pageContent, feeAmount, currency, acceptanceWindowDays}`.
   - `feeAmount` is **cents**.
   - **Explicit `currency`:** proposals default to `mxn`; milestones default to `usd`. Make them match.
   - `acceptanceWindowDays`: default 5, range 1–365.
   - Edit draft with `proposalId`, `expectedRevision` from `proposal_get`, `createNew:false`.
   - Only drafts are editable; sent/closed proposals retain content.
4. **Send:** `proposal_set_status {status:"sent"}` validates the SOW and starts acceptance window. **No email is sent**; the user notifies the client separately. Supply `expectedRevision` from `proposal_get`; on `CONFLICT`, reread.
5. **Client response:**
   - Client accepts/rejects in Portal (`proposal_accept` / `proposal_reject` are client-only, not staff).
   - Staff records an externally communicated response with `proposal_set_status {status:"accepted", acceptedByName, expectedRevision}` or `{status:"rejected", reason, expectedRevision}`.

   **Irreversible:** confirm the accepting person's exact name.
6. Link each billable milestone through `milestone_proposal_link {milestoneId, proposalId}`; feeds the next collection in Payments.

## CFDI income invoices (type I)

**Tax data comes from the stamped XML, never manual entry.** Issuer must be Pai's RFC or the server rejects it.

1. Optional PDF: `payment_file_upload {size}` with exact bytes, ≤10 MB; `PUT` PDF to `signedUrl` with `Content-Type: application/pdf` within 5 minutes; retain `uploadId`.
2. `payment_cfdi_import {xml, pdfUploadId?, milestoneId? | proposalId?, contract}`.
   - **Always supply `contract` for a milestone/proposal link:** `{currency, amount (cents), rate?, rateSource?}`, the contract-currency equivalent.
   - Without it, the invoice does not count toward payment status/totals; response warns.
3. Reimporting the same UUID returns the existing unchanged record; retry is safe.
4. **No CFDI edit/delete tool.** Check milestone, proposal, and `contract` before importing.

## Payments (payment complement, CFDI type P)

1. First import every invoice settled by the complement, in the same currency.
2. Upload complement PDF and transfer receipt separately through `payment_file_upload` → `PUT`.
3. `payment_record` with:
   - stable `requestId`, such as `pay-<project>-<complement-uuid>`; **reuse on retry**;
   - `complementXml`, optional `complementPdfUploadId`, `receiptUploadId`;
   - `paidAt`: bank execution date/time with zone;
   - `method`: `spei`, `transfer`, `card`, `cash`, `other`;
   - available `reference`, `trackingKey`, `payerName`, `payerBank`, `payerAccountLast4`…

   Store only the last four account digits.
4. Linked milestones become paid when invoices cover their amount. Verify `payment_list`.
5. Download receipt or invoice PDF/XML with `payment_file_download_url {fileId}` (`fileId` from `payment_list`). URL expires in 60 seconds: use immediately, never store/share.

## Void a payment

`payment_void {paymentId, reason}` voids an erroneous record and recalculates milestones. **Final**; already voided yields `CONFLICT`. Explain milestone effects before requesting confirmation.

## Avoid

- Never manually enter tax data (RFC, UUID, tax amounts); read XML.
- Never record payment before invoice import, or omit `contract` for a milestone-linked invoice.
- Never manually mark milestone `paymentStatus`; payments recalculate it.
- Never transition a proposal without explicit approval and the accepting person's name when applicable.
- Never delete projects/milestones with payments to clean up: `project_delete` cascades payments and CFDI.
