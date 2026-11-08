# Task 2: Document Q&A with RAG over WHO fact sheets

Part of the Datheon *Python + Generative AI & LangChain* internship.
Author: Sherifdeen Bilal Olamilekan

This is an educational demonstration of retrieval-augmented question answering. It is not medical advice.

## What was built

- A corpus of 12 public WHO fact sheets (URLs only; see "Data and licensing").
- A hand-written evaluation set of 12 questions: 3 specific-figure, 3 list, 2 multi-document comparisons and 4 unanswerable (2 near-miss/absent topics, 2 out of scope), each labelled with a document and a short anchor phrase.
- Two retrievers compared on the labelled passages: BM25 and dense embeddings (a local model, no LLM quota).
- Answer generation with Gemini (`gemini-3.7-flash`, temperature 0) in two conditions: with the top 3 dense chunks, and with no retrieval. Answers were graded by hand.
- Predictions were written and committed before any retrieval or generation was run (`PREDICTIONS.md`).

Full results are in `RESULTS.md` and the per-question grades in `GRADING.md`.

## Headline results (observed; 8 answerable questions; directional only)

| Measure | BM25 | Dense |
|---|---|---|
| Labelled passage in top 3 (hit@3), Q1 to Q8 | 3/8 | 6/8 |
| MRR, single-document questions Q1 to Q6 | 0.389 | 0.806 |

| Answers, Q1 to Q8 | Correct | Partial | Wrong |
|---|---|---|---|
| With retrieval (dense, top 3) | 5 | 1 | 2 |
| No retrieval, conservative reading | 3 | 0 | 5 |
| No retrieval, lenient reading of two borderline items | 5 | 0 | 3 |

- With retrieval, all 4 unanswerable questions were answered with a correct abstention, including the Ebola near-miss.
- Without retrieval, the figures for Q1 to Q3 were from earlier years than the corpus snapshot.
- Both retrievers failed on the two comparison questions, and the retrieval condition abstained on them because only one of the two documents was retrieved.
- Retrieval with a strict "only the passages" instruction did not clearly beat the no-retrieval condition on answer correctness for this small set; its advantages were current figures, grounding and abstention.

## Files

| File | Purpose |
|---|---|
| `urls.txt` | The 12 source URLs |
| `fetch_corpus.py` | Downloads the pages to `data/` and writes `data/manifest.json` |
| `clean_corpus.py` | Removes reference lists and footnote lines; writes `data/corpus_clean.json` |
| `find_passage.py` | Prints text around a search term, for locating passages when labelling |
| `questions.jsonl` | The 12 labelled questions |
| `validate_questions.py` | Checks anchors, gold items and probe words against the corpus |
| `retrieve.py` | BM25 and dense retrieval with fixed settings; writes `retrieval_results.json` |
| `diagnose.py` | Exploratory per-passage and per-document ranks (not pre-registered) |
| `answer.py` | Generates answers in both conditions, with caching and frozen retrieval |
| `PREDICTIONS.md` | Predictions committed before any results existed (not edited since) |
| `RESULTS.md` | Retrieval and generation results, snapshot notes and limitations |
| `GRADING.md` | Grading rules and the hand-assigned grade for every answer |
| `retrieval_results.json` | Retrieval ranks from the 2026-11-06 snapshot |
| `frozen_retrieval.json` | The top 3 chunks (document, chunk number, text hash) used for generation; no page text |
| `answers.json` | The generated answers |
| `corpus_manifest.json` | URL, status, word count and hash per page for the 2026-11-06 download |

## Data and licensing

WHO web content carries a general copyright notice, so this repository contains **URLs only**. The page text is downloaded locally and kept out of version control (`data/` is git-ignored). `frozen_retrieval.json` stores chunk positions and hashes, not text. The generated answers are short model outputs.

## How to reproduce

```text
pip install -r requirements.txt
python fetch_corpus.py urls.txt
python clean_corpus.py
python validate_questions.py questions.jsonl
python retrieve.py
export GEMINI_API_KEY=your_key_here
python answer.py --dry
python answer.py
```

- `answer.py` reads the retrieved chunks from `frozen_retrieval.json` (in Colab it uses a copy on Google Drive) and caches every answer, so re-running never repeats a request. Fact sheets change over time, so re-fetching later may produce different text; the hashes in `frozen_retrieval.json` make `answer.py` stop if the chunks no longer match.
- The first run downloads the embedding model `sentence-transformers/all-MiniLM-L6-v2`.

## Corpus snapshots

The corpus was downloaded on 2026-10-30 (questions, labels, first retrieval run) and again on 2026-11-06 after a Colab runtime reset (generation). The 2026-10-30 manifest was not saved; its word counts below come from the printouts of that day.

| Document | Raw words 10-30 | Raw words 11-06 | Cleaned words 10-30 | Cleaned words 11-06 |
|---|---|---|---|---|
| hypertension | 1357 | 1357 | 1357 | 1357 |
| diabetes | 1245 | **1239** | 1217 | 1217 |
| obesity and overweight | 2027 | 2027 | 1880 | 1880 |
| physical activity | 1426 | **1419** | 1349 | **1321** |
| tobacco | 1608 | 1608 | 1476 | 1476 |
| alcohol | 1571 | 1571 | 1571 | 1571 |
| air pollution | 1183 | 1183 | 1175 | 1175 |
| depression | 1248 | 1248 | 1149 | 1149 |
| malaria | 1941 | 1941 | 1939 | 1939 |
| tuberculosis | 1738 | 1738 | 1738 | 1738 |
| immunization coverage | 1629 | 1629 | 1628 | 1628 |
| antimicrobial resistance | 1477 | 1477 | 1433 | 1433 |

- Physical activity changed in its body text; WHO's page is dated 4 November 2026.
- Diabetes differs by 6 raw words, but its cleaned word count is identical, so the difference lies in the part removed by cleaning (references or related links). A wording change in the body cannot be fully excluded.
- Retrieval was re-run on the 2026-11-06 snapshot. Every per-question rank and group metric matched the first run; only some top-3 document lists for unanswerable questions changed (see `RESULTS.md`).

## Run history for generation (provenance)

Generation was interrupted by the free-tier daily quota (20 requests per model per day) and by temporary server overloads, and was resumed from the answer cache:

1. 15 requests: retrieval answers Q1 to Q12 and no-retrieval Q1 to Q3.
2. 1 request: no-retrieval Q4.
3. Two attempts blocked by server overload (no requests made).
4. 4 requests: the retrieval prompts for Q5 and Q11 had changed (see below), so they were regenerated, plus no-retrieval Q5 and Q6.
5. 6 requests: no-retrieval Q7 to Q12.

The retrieval prompts for Q5 and Q11 differed between the first run and later runs. For Q11 the physical-activity page had changed; for Q5 the cause is not established (most likely small numerical differences between runtimes). To stop this recurring, the chosen chunks were frozen in a file (`answer.py` v2). The first-run answers for Q5 and Q11 were also abstentions and are recorded in `GRADING.md`. The final six requests (no-retrieval Q7 to Q12) ran with an earlier copy of `answer.py` that lacked the freeze logic; no-retrieval prompts contain no retrieved text, so they are unaffected.

## Limitations

- Small evaluation set (8 answerable and 4 unanswerable questions); every difference is directional.
- Q4 to Q6 were deliberately reworded to avoid the source's key terms, which favours dense retrieval by design.
- The hit definition is strict (one anchored passage), so it may understate a retriever that returns other relevant chunks.
- The answer-matching rule (equivalent meaning, at least 60% of gold items) was defined after the answers were seen, and the conservative and lenient readings differ for two questions. Grading was done by one person.
- One chunking setup, one embedding model, one LLM and one prompt were tested at temperature 0; LLM answers may vary between runs.
- The no-retrieval prompts for Q9 and Q10 do not mention supplied documents, so a general-knowledge answer is not a fair abstention test for that condition.
- Fact sheets are updated over time; results apply to the 2026-10-30 and 2026-11-06 snapshots.

## Possible next steps

Retrieving per document for comparison questions, testing other chunk sizes as clearly labelled new experiments, using similarity scores as an abstention signal, a looser answer prompt, and a larger question set.
