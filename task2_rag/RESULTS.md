# Retrieval Results

The question set and predictions (`PREDICTIONS.md`) were committed before any retrieval was run; see the git history. The settings below were fixed in `retrieve.py` and were not tuned after seeing results.

All numbers are observed on a small evaluation set (8 answerable questions) and are directional only.

## Method

- Corpus: 12 WHO fact sheets, accessed 2026-10-30; 178 chunks of 150 words with a 100-word step.
- BM25: `rank_bm25` BM25Okapi with default parameters, lowercase alphanumeric tokens and a small stopword list.
- Dense: local model `sentence-transformers/all-MiniLM-L6-v2`, cosine similarity.
- Top 10 results per retriever.
- **Hit definition (strict):** a retrieved chunk from the labelled document contains the question's anchor, a short phrase from one labelled passage. For the two comparison questions (Q7, Q8) the anchors of both documents must appear. Hit@1 is therefore impossible for Q7 and Q8.
- MRR is computed on the single-document questions (Q1 to Q6) only.

## Summary (answerable questions Q1 to Q8)

| Metric | BM25 | Dense |
|---|---|---|
| hit@1 | 2/8 | 4/8 |
| hit@3 | 3/8 | 6/8 |
| hit@5 | 3/8 | 6/8 |
| MRR (Q1 to Q6) | 0.389 | 0.806 |

Dense retrieval placed the labelled passage in its top 3 for all six single-document questions; BM25 did so for three. Neither retriever retrieved both passages for either comparison question.

## Evaluation against the pre-registered predictions

| Prediction | Observed | Outcome |
|---|---|---|
| P1: BM25 ranks the Ebola passage first | BM25 rank 2 | Not met |
| P1: dense places it in its top 3 | Dense rank 1 | Met |
| P1: generator abstains instead of inventing guidance | Not yet tested | Pending |
| P2: dense beats BM25 by at least 2 questions at hit@3 on paraphrased questions (Q1, Q4, Q5, Q6) | Dense 4, BM25 2 (n = 4) | Met, exactly at the threshold |
| P3: BM25 hit@1 is at least dense hit@1 on Q2 and Q3 | 1 vs 1 | Met as a tie |
| P4: hit@3 of 7/8 for BM25 and 7/8 for dense | BM25 3/8, dense 6/8 | Not met for either |
| P4: no-retrieval baseline answers 3/8 correctly | Not yet tested | Pending |

Notes:
- P3 was met only as a tie. BM25 retrieved the right document for Q3 at rank 1 but not the labelled passage (not in the top 10), while dense retrieved the labelled passage at rank 2. The reasoning behind the prediction, that BM25 would have an edge on distinctive figures and terms, was not supported.
- P4: both estimates were over-optimistic, BM25 by a large margin. This is recorded as a calibration error.

## Exploratory diagnostics (not pre-registered)

Rank of the labelled passage, and of its document, within the top 10 (None = not in the top 10).

| Question | Labelled document | BM25 passage | Dense passage | BM25 document | Dense document |
|---|---|---|---|---|---|
| Q1 | hypertension | 1 | 1 | 1 | 1 |
| Q2 | tuberculosis | 1 | 1 | 1 | 1 |
| Q3 | malaria | None | 2 | 1 | 1 |
| Q4 | hypertension | 3 | 1 | 3 | 1 |
| Q5 | diabetes | None | 3 | 1 | 1 |
| Q6 | antimicrobial resistance | None | 1 | 1 | 1 |
| Q7 | diabetes | None | None | 2 | 4 |
| Q7 | obesity | None | 6 | 1 | 1 |
| Q8 | tobacco | None | 4 | None | 1 |
| Q8 | alcohol | None | None | 1 | 8 |

Observations:
- For all six single-document questions, BM25 ranked the correct document within its top 3 (ranks 1, 1, 1, 3, 1, 1), and dense ranked it first. The gap between the retrievers is therefore at the level of choosing the passage inside the right document, not identifying the document.
- The hit definition is strict (one anchored passage). Other chunks from the same document may contain relevant content, for example the risk factors for Q4 appear in more than one place on the page. The strict metric may understate BM25; answer quality in the generation step is the better test.
- Q7 and Q8: dense found one of the two required passages in each (obesity at rank 6 for Q7; tobacco at rank 4 for Q8). BM25 found neither labelled passage, although for Q7 it ranked both documents in its top 2.
- Why the comparison questions failed has not been diagnosed. Alternative chunking or retrieving per document were not tested.

## Unanswerable and near-miss questions

| Question | BM25 top-3 documents | Dense top-3 documents |
|---|---|---|
| Q9 (Ebola treatment, near-miss) | hypertension, immunization, tuberculosis (Ebola chunk at rank 2) | immunization, immunization, antimicrobial resistance (Ebola chunk at rank 1) |
| Q10 (sickle cell) | hypertension, air pollution, obesity | immunization (three chunks) |
| Q11 (budget) | hypertension, diabetes, depression | tuberculosis, tuberculosis, physical activity |
| Q12 (salary) | alcohol, antimicrobial resistance, physical activity | tuberculosis (three chunks) |

Both retrievers return plausible-looking passages even when the corpus contains nothing relevant, so retrieval alone does not signal that a question is unanswerable. Abstention has to be evaluated at the generation step.

## Limitations

- Small evaluation set (n = 8 answerable, 4 unanswerable); all differences are directional.
- Q4 to Q6 were deliberately reworded to avoid the source's key terms, which favours dense retrieval by design. BM25 and dense were run with default settings and no tuning.
- The strict anchor-based hit definition understates retrievers that return other relevant chunks from the right document.
- One chunking configuration and one embedding model were tested.
- Fact sheets change over time; results apply to the snapshot accessed on 2026-10-30.

## Not yet done

Answer generation (with retrieval and without) and abstention on Q9 to Q12.
