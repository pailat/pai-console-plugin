---
name: proposals-payments
description: Propuestas (SOW) y cobros de un proyecto de Pai Console. Cubre redactar y guardar la propuesta, enviarla y registrar su aceptación o rechazo, ligar hitos a la propuesta, importar CFDI (facturas de ingreso), registrar pagos desde el complemento de pago y anular pagos. Úsalo cuando pidan propuesta, cotización, SOW, inversión, factura, CFDI, complemento de pago, pago recibido, cobro o anulación.
argument-hint: "[proyecto] [propuesta, factura o pago]"
compatibility: "Pai 0.2.5+ (MCP corp)"
---

# Propuestas y Pagos en Pai

Lee antes el skill `pai-console`. Aquí casi todo mueve dinero o compromisos con el cliente.

**Las transiciones de propuesta, los CFDI y los pagos no se deshacen** (salvo anular un pago, que también es definitivo). Antes de cada una, di a la persona exactamente qué vas a registrar y espera su sí explícito, también en staging.

## Propuestas

Una propuesta es un SOW: su `pageContent` sigue el contrato de pages con el tipo **`sow`**. Las secciones van en este orden y son todas obligatorias:

| Sección | Bloques permitidos |
|---|---|
| `contexto` | text, callout |
| `alcance` | deliverables, text |
| `fuera-de-alcance` | text, cards |
| `plan` | timeline, steps, text |
| `inversion` | data-table, facts, text |
| `supuestos` | text, callout, risks |
| `fuentes` | sources |

Bloques obligatorios en algún lugar del documento: `deliverables`, `data-table` y `sources`. Detalle en `../resources/references/page-types.md`.

1. **Lee** `proposal_list` y, si hay propuesta, `proposal_get`. Un proyecto tiene historial de propuestas; un borrador vivo se edita, no se duplica.
2. **Compón el SOW:**
   - `deliverables`, cada uno con su criterio de aceptación;
   - `fuera-de-alcance` explícito: es lo que evita disputas;
   - la inversión en un `data-table` con su fuente;
   - los supuestos.

   Valida con `page_validate {content, typeSlug:"sow"}`.
3. **Guarda:** `proposal_save` con `{organizationId, projectId, createNew:true, title, pageContent, feeAmount, currency, acceptanceWindowDays}`.
   - `feeAmount` va **en centavos**.
   - `currency` **explícita**: por defecto es `mxn`, pero los hitos usan `usd` por defecto. Que coincidan.
   - `acceptanceWindowDays` vale 5 por defecto (de 1 a 365).
   - Para editar el borrador: `proposalId` + `expectedRevision` de `proposal_get`, y `createNew:false`.
   - Solo se editan borradores. Las propuestas enviadas o cerradas conservan su contenido.
4. **Enviar:** `proposal_set_status {status:"sent"}`.
   - Valida el SOW y arranca la ventana de aceptación.
   - **No manda correo:** la persona avisa al cliente por su canal.
   - Manda `expectedRevision` (la `revision` de `proposal_get`): si cambió, responde `CONFLICT` y hay que volver a leer.
5. **Respuesta del cliente**, por una de dos vías:
   - el cliente la acepta o rechaza en el Portal (`proposal_accept` / `proposal_reject` son del cliente, no del staff);
   - el staff registra lo que el cliente comunicó por otro medio: `proposal_set_status {status:"accepted", acceptedByName, expectedRevision}` o `{status:"rejected", reason, expectedRevision}`.

   **Irreversible:** confirma el nombre exacto de quien aceptó.
6. **Liga cada hito que cobra** con `milestone_proposal_link {milestoneId, proposalId}`. Alimenta el «siguiente cobro» de Pagos.

## CFDI (facturas de ingreso, tipo I)

**Los datos fiscales salen del XML timbrado:** nunca los escribas tú. El emisor debe ser el RFC de Pai; si no lo es, el servidor rechaza la factura.

1. **PDF (opcional):**
   - `payment_file_upload {size}` con los bytes exactos, ≤10 MB;
   - `PUT` del PDF a `signedUrl` con `Content-Type: application/pdf` antes de 5 min;
   - guarda el `uploadId`.
2. **`payment_cfdi_import`** con `{xml, pdfUploadId?, milestoneId? | proposalId?, contract}`.
   - **Siempre `contract` cuando la ligas a un hito o a una propuesta:** `{currency, amount (centavos), rate?, rateSource?}`, la equivalencia en la moneda del contrato.
   - Sin `contract`, la factura no cuenta para el estado de pago ni para los totales; la respuesta lo advierte.
3. Reimportar el mismo UUID devuelve el registro existente sin cambios: es seguro reintentar.
4. **No hay herramienta para editar ni borrar un CFDI.** Revisa hito, propuesta y `contract` antes de importar.

## Pagos (complemento de pago, CFDI tipo P)

1. **Antes,** cada factura que liquida el complemento debe estar importada, y en la misma moneda.
2. **PDFs** del complemento y del comprobante de transferencia: `payment_file_upload` → `PUT` en cada uno.
3. **`payment_record`** con:
   - `requestId`: estable, por ejemplo `pay-<proyecto>-<uuid-del-complemento>`; **reutilízalo al reintentar**;
   - `complementXml`, `complementPdfUploadId?`, `receiptUploadId?`;
   - `paidAt`: fecha y hora con zona, la de la ejecución bancaria;
   - `method`: `spei`, `transfer`, `card`, `cash` u `other`;
   - y, si los tienes, `reference`, `trackingKey`, `payerName`, `payerBank`, `payerAccountLast4`…

   De las cuentas solo se guardan los últimos 4 dígitos.
4. Los hitos ligados pasan a **pagados** cuando sus facturas cubren su monto. Verifica con `payment_list`.
5. Para descargar un comprobante o el PDF/XML de una factura: `payment_file_download_url {fileId}` (el `fileId` viene de `payment_list`). La URL dura 60 s: úsala de inmediato y no la guardes ni la compartas.

## Anular un pago

`payment_void {paymentId, reason}` anula un pago registrado por error y recalcula los hitos. Es **definitivo**: si ya estaba anulado, da `CONFLICT`. Explica a la persona el efecto en los hitos antes de pedir su confirmación.

## Qué no hacer

- **No** escribas datos fiscales (RFC, UUID, montos de impuestos) a mano: salen del XML.
- **No** registres un pago sin sus facturas importadas, ni importes sin `contract` una factura ligada a un hito.
- **No** marques `paymentStatus` de un hito a mano: lo recalculan los pagos.
- **No** cambies el estado de una propuesta sin una confirmación explícita de la persona, con el nombre de quien aceptó.
- **No** borres un proyecto ni un hito con pagos para «limpiar»: `project_delete` borra en cascada pagos y CFDI.
