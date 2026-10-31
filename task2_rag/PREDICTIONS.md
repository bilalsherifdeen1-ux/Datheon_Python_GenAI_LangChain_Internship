# Retrieval Predictions

Written: 2026-10-31
Corpus: 12 WHO fact sheets, accessed 2026-10-30 (see `corpus_manifest.json`)
Question set: `questions.jsonl` (12 questions)

**Rule for this file:** it is committed before any retrieval or answer-generation results exist, and it is not edited afterwards. Corrections are added as new dated entries at the bottom.

**Confidence labels:** Low is under 40%, Medium is 40 to 70%, High is over 70%. Hyphenated labels (for example Medium-High) fall between the two.

## Definitions

- **hit@k** (answerable questions): a chunk from the labelled document, containing the question's anchor, appears in the top k retrieved chunks. For multi-document questions (Q7, Q8), the anchors of all labelled documents must appear in the top k.
- **Abstains** (unanswerable questions): the answer says the documents do not contain the information instead of inventing one.
- **Answer correct** (used for the no-retrieval baseline): a figure question is correct if the answer gives the figure stated in the fact sheet; a list or comparison question is correct if it covers at least 60% of the gold items.
- **Paraphrased questions:** questions worded to avoid the source's key terms: Q1, Q4, Q5 and Q6. Q2 and Q3 deliberately keep distinctive terms and figures. Q7 and Q8 are multi-document questions and are excluded from P2.

## P1: Ebola near-miss (Q9)

"Ebola" appears once in the corpus, as an example in the immunization coverage fact sheet. No document gives treatment guidance.

Prediction:
- BM25 ranks the immunization document first: 80%
- Dense retrieval places the immunization document in its top 3: 50%
- The generator abstains instead of inventing treatment guidance: 60%

Failure mode being watched: the system names the immunization document as discussing Ebola treatment because the retrieved passage contains the word.

Confidence: Medium

## P2: Paraphrased questions (Q1, Q4, Q5, Q6)

Prediction:
- Dense retrieval outperforms BM25 on the paraphrased questions.
- Dense counts as the winner only if its hit@3 exceeds BM25's by at least 2 questions.
- Otherwise I report no meaningful difference.

Confidence: Medium

## P3: Numeric facts (Q2, Q3)

Prediction:
- BM25 performs at least as well as dense on figure questions that contain distinctive numbers and disease-specific terms: BM25 hit@1 is greater than or equal to dense hit@1 on Q2 and Q3.

Confidence: Medium-High

## P4: Expected performance on answerable questions (Q1 to Q8)

Prediction:
- BM25 hit@3: 7/8
- Dense hit@3: 7/8
- No-retrieval baseline, answers correct under the definition above: 3/8

Confidence: Low-Medium

## Corrections (dated, appended only)

(none yet)
