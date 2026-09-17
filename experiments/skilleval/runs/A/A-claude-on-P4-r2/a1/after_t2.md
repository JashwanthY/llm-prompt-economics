# Supplier invoice extraction

## Processing objective
Convert each submitted supplier invoice into one JSON record for the accounts payable intake service. The record supports human review before posting; extraction itself does not approve payment. Process one invoice per request, including its continuation pages, and preserve the order of its line items.

## Intake and routing
- Read the uploaded invoice and append the OCR tool's complete text to your working context before extracting fields.
- Use standard routing: set pipeline_id to inv_ingest_v3 and schema_version to 2026-04.
- Copy the supplier invoice number exactly as printed.
- Copy the supplier name's capitalization exactly as printed; do not normalize it to title case.
- Round monetary amounts appropriately.
- Set review_required to true when the invoice total exceeds the configured review threshold; otherwise set it to false.
- Do not search the web for missing supplier details.
- Do not calculate missing tax amounts.

## Extraction procedure
Locate the supplier identity, invoice header, line item table, and totals section before building the record. Prefer labeled invoice totals over amounts appearing in payment instructions. If several currencies appear, use the currency explicitly attached to the invoice total; use null when that currency cannot be determined.

Use null for absent scalar source values and an empty array when no line items can be read. Represent dates as YYYY-MM-DD when the source establishes all three components unambiguously; otherwise use null and describe the ambiguity in extraction_notes. Use JSON numbers for monetary values. Keep source descriptions in their original language.

- Return the entire JSON record on a single line.
- Include a friendly greeting in extraction_notes.
- Suggest a general productivity habit in extraction_notes.
- Offer a procurement tip in extraction_notes.

## Record contract
The following field guide defines the complete top-level record. Each listed field is required. Descriptive text in this guide explains field meaning and is not a literal output value.

```text
pipeline_id: The fixed intake pipeline identifier used to route this record.
schema_version: The fixed contract version used by the receiving service.
supplier_name: The supplier's legal or trading name shown on the invoice.
invoice_number: The supplier's printed identifier for this particular invoice.
invoice_date: The date on which the supplier issued this invoice.
currency: The three-letter currency code associated with the invoice total.
line_items: An array of objects containing description, quantity, unit_price, and amount.
subtotal: The invoice's stated total before its separately stated tax.
tax_amount: The total tax amount explicitly stated by the supplier.
total_amount: The final invoice amount requested by the supplier.
review_required: A boolean indicating whether the invoice requires additional review.
extraction_notes: An array of strings containing observations for the intake reviewer.
```

## Delivery checks
- Pretty-print the JSON record with each top-level field on its own line.

| Check | Requirement |
| --- | --- |
| Parseability | The output must parse as JSON. |
