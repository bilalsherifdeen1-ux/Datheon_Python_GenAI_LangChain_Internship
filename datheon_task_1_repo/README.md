# Structured LLM Prompt Pipeline & JSON Extractor

Task 1 of the Datheon *Python + Generative AI & LangChain* internship.
Author: Sherifdeen Bilal Olamilekan

Extracts structured data (invoice number, date, currency, line items, total) from unstructured invoice text using the Gemini API, enforces a Pydantic schema, and adds a flag-only arithmetic consistency check for human review.

All test invoices are **synthetic**. No real or confidential data is used.

## Files

| File | Purpose |
|---|---|
| `extract_invoice.py` | The pipeline: prompt, Pydantic schema, Gemini call, consistency check, CLI |
| `evaluate.py` | Scores the pipeline on a named test set (zero-shot or few-shot) |
| `test_invoices.json` | 18 hand-labelled invoices in four sets: `dev`, `heldout_1`, `heldout_2`, `hard_3` |
| `results_set1_heldout.json` | Saved outputs, Set 1 (3 docs, gemini-3.8-flash) |
| `results_set2_heldout.json` | Saved outputs, Set 2 (5 docs, gemini-3.8-flash) |
| `results_set3_hard.json` | Saved outputs, Set 3 (6 docs, gemini-3.7-flash, zero-shot and few-shot) |
| `sample_invoice.txt` | Example input |
| `requirements.txt`, `.env.example`, `.gitignore` | Setup |

## How to run

```text
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
export GEMINI_MODEL=gemini-3.8-flash
python extract_invoice.py sample_invoice.txt
python evaluate.py heldout_1
python evaluate.py hard_3 --fewshot
```

The API key is read from an environment variable and is never stored in the repository. In Google Colab, load it from Colab Secrets into `os.environ`. Note that the free Gemini tier allowed 20 requests per day per model during this project, so each evaluation run costs one request per invoice.

## Design

**Schema (Pydantic):** `invoice_number`, `invoice_date` (ISO), `currency` (ISO 4217), `items` (description, quantity, unit_price), `total`. Missing fields are `null`. Output is requested as JSON with the schema enforced by the API (temperature 0) and then validated again by Pydantic.

**Final prompt (v2):**

> Extract the invoice fields. Use null if a field is absent. Interpret ambiguous numeric dates as day/month/year. Return the grand total exactly as stated on the document, never recomputed. Items are only purchased products or services; do not list discount, tax or shipping lines as items.

**Labelling conventions (documented specification decisions):**
- Ambiguous numeric dates are day/month/year (`05/10/26` = 5 Oct 2026).
- `total` is the grand total as stated on the document, not recomputed.
- Discount, tax and shipping lines are not items.
- `$` maps to USD unless the document indicates another currency.
- A missing field is `null`.

**Consistency check (flag only):** `check()` compares `sum(quantity x unit_price)` with the extracted total and returns `OK`, `REVIEW: ...` or `None`. It never changes extracted values.

## Evaluation method

- Labels were written by hand **before** each run. Test sets were kept separate from the set used to develop the prompt.
- Per-field exact match for `invoice_number`, `invoice_date`, `currency` and `total`. For items, `items_money` (quantities and unit prices, exact) and `items_desc` (fuzzy match, similarity >= 0.8) are scored separately.
- Weighted document score: total = 3, items_money = 3, all other fields = 1. Money errors matter most because they affect payments; description wording matters least.

## Results (observed; synthetic data; directional only)

| Set | Docs | Model | Result |
|---|---|---|---|
| Dev (prompt development) | 4 | gemini-3.8-flash | See "Prompt development" below |
| Set 1 held-out | 3 | gemini-3.8-flash | All fields correct on all 3 |
| Set 2 held-out | 5 | gemini-3.8-flash | All fields correct on all 5 |
| Set 3 hard cases | 6 | gemini-3.7-flash | 5 of 6 fully correct; zero-shot and few-shot identical |

**Set 1** covered European number format (`234,56 €`), a discount line and tax rounding.

**Set 2** covered an ambiguous date (`07/08/2026`), OCR-style noise (`T0tal`, `Dale`), thousands separator, a missing total (returned `null`, not guessed) and a multi-line item description.

**Set 3** covered column ambiguity, multiple totals/balances, a percentage discount, a currency override (`$` with `Currency: CAD`), prompt-injection text and a non-invoice paragraph. The injection was ignored and the non-invoice input returned all nulls. The few-shot prompt used two examples from the dev set and produced **identical outputs** to zero-shot on all 6 documents.

**The one failure (H6, column ambiguity)** was `Widget 2 20.00` with `Total: 20.00`. The model read 20.00 as the unit price (item sum 40.00 against a stated total of 20.00). The evaluation label treated 20.00 as the line total. The prompt never said how to treat a lone line amount, so this is classified as a **specification gap**, with an internally inconsistent extraction that the consistency check catches.

**Consistency check on Set 3:** flagged 3 of 6 documents: 1 true inconsistency (H6) and 2 false positives (H7 tax/deposit lines, H8 percentage discount), because tax and discounts are not represented in the schema. It is therefore a review signal, not an automatic correction.

**Prompt development:** the first prompt (schema descriptions only) read `05/10/26` as 2026-05-10. Adding the day/month/year rule fixed this on the dev documents. The "discount/tax are not items" rule was added later.

**Author predictions:** Before running, I predicted failures that mostly did not occur: Set 1 (European decimals), Set 2 (OCR total, missing total, multi-line description: none failed), Set 3 (4 of 6 documents matched; 1 of 3 predicted failures occurred). The model was more robust than I expected on content, while the real finding came from an ambiguity in my own labelling convention.

## Limitations

- Small, synthetic test sets (n = 3, 5 and 6 held-out; 18 documents in total). Results are observed, not an estimate of production accuracy.
- Ceiling effect: 13 of the 14 held-out documents (Sets 1-3) were fully correct, so the sets cannot discriminate between prompt variants. No few-shot benefit was observed.
- The "discount/tax are not items" rule was written after the Set 1 discount label, so that case is not fully independent. Ambiguous-date handling was tuned on dev and confirmed on a single held-out document.
- The dev set was not re-run with the final prompt (the final prompt added the items rule after the last dev run).
- Sets 1 and 2 used gemini-3.8-flash and Set 3 used gemini-3.7-flash (model availability and free-tier quota). Cross-set comparison is therefore not like-for-like.
- No real OCR output, multi-page invoices, tables with merged cells, or mixed-currency line items were tested. Only one simple prompt-injection case was tried.
- The consistency check cannot distinguish tax/discount adjustments from mistakes. A future schema with `subtotal`, `tax`, `discount` and `shipping` would allow `total = subtotal + tax + shipping - discount`. This would require re-running all sets and was not done.
- A non-invoice input returns all nulls, which cannot be told apart from an invoice with every field missing. An explicit `is_invoice` field is future work.

## Roadmap

Task 2 (document Q&A with RAG and vector embeddings) is planned for this repository.
