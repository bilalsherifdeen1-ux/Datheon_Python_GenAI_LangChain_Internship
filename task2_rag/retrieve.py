import json, re, sys
import numpy as np
from rank_bm25 import BM25Okapi
CONFIG = {"chunk_words": 150, "stride_words": 100, "top_k": 10, "dense_model": "sentence-transformers/all-MiniLM-L6-v2", "bm25": "rank_bm25 BM25Okapi (k1=1.5, b=0.75), lowercase alphanumeric tokens, small stopword list", "questions": "questions.jsonl", "corpus": "data/corpus_clean.json"}
STOP = set("a an and are as at be by for from has have in is it of on or that the to was were with which who what how many do does can".split())
def norm(s): return re.sub(r"\s+", " ", s.replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ").replace("\u202f", " ").replace("\u2019", "'").lower()).strip()
def tok(s): return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOP]
RAW = {k: " ".join(v["paragraphs"]) for k, v in json.load(open(CONFIG["corpus"], encoding="utf-8")).items()}
TXT = {k: norm(t) for k, t in RAW.items()}
Q = [json.loads(l) for l in open(CONFIG["questions"], encoding="utf-8") if l.strip()]
def pairs(q): return list(zip(q["docs"], q["anchors"])) if len(q["docs"]) == len(q["anchors"]) else [(q["docs"][0], a) for a in q["anchors"]]
BAD = [(q["id"], d, a[:30], c) for q in Q if q["answerable"] for d, a in pairs(q) for c in [TXT.get(d, "").count(norm(a))] if c != 1] + [(q["id"], "TODO") for q in Q if q["question"].strip() == "TODO"]
BAD and sys.exit("Fix the labels first (id, doc, anchor, count): " + str(BAD))
def chunks(doc, text): w = text.split(); return [(doc, i, " ".join(w[s:s + CONFIG["chunk_words"]])) for i, s in enumerate(range(0, max(1, len(w) - CONFIG["chunk_words"] + CONFIG["stride_words"]), CONFIG["stride_words"]))]
CH = [c for d, t in RAW.items() for c in chunks(d, t)]
print("config:", json.dumps(CONFIG)); print("docs:", len(RAW), "| chunks:", len(CH), "| questions:", len(Q))
def rank(scores): return [int(i) for i in np.argsort(-np.asarray(scores, dtype=float), kind="stable")[:CONFIG["top_k"]]]
def embedder(): from sentence_transformers import SentenceTransformer; return SentenceTransformer(CONFIG["dense_model"])
EMB = embedder()
E = EMB.encode([c[2] for c in CH], normalize_embeddings=True, show_progress_bar=False)
BM = BM25Okapi([tok(c[2]) for c in CH])
def top_bm25(qtext): return rank(BM.get_scores(tok(qtext)))
def top_dense(qtext): return rank(E @ EMB.encode([qtext], normalize_embeddings=True, show_progress_bar=False)[0])
def hit(ci, d, a): return CH[ci][0] == d and norm(a) in norm(CH[ci][2])
def k_needed(top, q): return next((k for k in range(1, len(top) + 1) if all(any(hit(ci, d, a) for ci in top[:k]) for d, a in pairs(q))), None)
def probe_rank(top, q): return next((r for r, ci in enumerate(top, 1) if any(norm(p) in norm(CH[ci][2]) for p in q.get("probe", []))), None)
RES = {q["id"]: {"type": q["type"], "answerable": q["answerable"], "bm25": top_bm25(q["question"]), "dense": top_dense(q["question"])} for q in Q}
ANS = [q for q in Q if q["answerable"]]
for q in Q: RES[q["id"]].update({"bm25_k": k_needed(RES[q["id"]]["bm25"], q) if q["answerable"] else None, "dense_k": k_needed(RES[q["id"]]["dense"], q) if q["answerable"] else None, "bm25_probe_rank": probe_rank(RES[q["id"]]["bm25"], q) if q.get("probe") else None, "dense_probe_rank": probe_rank(RES[q["id"]]["dense"], q) if q.get("probe") else None, "bm25_top3_docs": [CH[i][0] for i in RES[q["id"]]["bm25"][:3]], "dense_top3_docs": [CH[i][0] for i in RES[q["id"]]["dense"][:3]]})
def hk(ids, m, k): return sum(1 for i in ids if RES[i][m + "_k"] is not None and RES[i][m + "_k"] <= k)
def mrr(ids, m): return round(sum((1 / RES[i][m + "_k"]) if RES[i][m + "_k"] else 0 for i in ids) / len(ids), 3)
G = {"answerable_Q1_Q8": [q["id"] for q in ANS], "single_doc_Q1_Q6": [q["id"] for q in ANS if q["type"] in ("figure", "list")], "paraphrased_Q1_Q4_Q5_Q6": ["Q1", "Q4", "Q5", "Q6"], "figure_terms_Q2_Q3": ["Q2", "Q3"]}
print("\nper question (k = smallest top-k that contains the labelled passage(s); None = not in top", CONFIG["top_k"], ")")
_ = [print(q["id"], q["type"], "| BM25 k:", RES[q["id"]]["bm25_k"], "| dense k:", RES[q["id"]]["dense_k"]) for q in ANS]
print("\ngroup results (hit@1 / hit@3 / hit@5)")
_ = [print(g, "| n =", len(ids), "| BM25:", hk(ids, "bm25", 1), hk(ids, "bm25", 3), hk(ids, "bm25", 5), "| dense:", hk(ids, "dense", 1), hk(ids, "dense", 3), hk(ids, "dense", 5)) for g, ids in G.items()]
print("MRR single-doc Q1-Q6 | BM25:", mrr(G["single_doc_Q1_Q6"], "bm25"), "| dense:", mrr(G["single_doc_Q1_Q6"], "dense"))
print("\nunanswerable / near-miss questions (top-3 documents; rank of the first chunk containing a probe word)")
_ = [print(q["id"], q["type"], "| BM25 docs:", RES[q["id"]]["bm25_top3_docs"], "probe rank:", RES[q["id"]]["bm25_probe_rank"], "| dense docs:", RES[q["id"]]["dense_top3_docs"], "probe rank:", RES[q["id"]]["dense_probe_rank"]) for q in Q if not q["answerable"]]
P = G["paraphrased_Q1_Q4_Q5_Q6"]; F = G["figure_terms_Q2_Q3"]
print("\nprediction checks (raw measures only)")
print("P1 Q9: BM25 probe rank:", RES["Q9"]["bm25_probe_rank"], "| dense probe rank:", RES["Q9"]["dense_probe_rank"], "(generator abstention is checked later by hand)")
print("P2 paraphrased hit@3: dense", hk(P, "dense", 3), "vs BM25", hk(P, "bm25", 3), "| difference", hk(P, "dense", 3) - hk(P, "bm25", 3), "| rule (dense wins if difference >= 2):", "dense wins" if hk(P, "dense", 3) - hk(P, "bm25", 3) >= 2 else "no meaningful difference")
print("P3 Q2,Q3 hit@1: BM25", hk(F, "bm25", 1), "vs dense", hk(F, "dense", 1), "| BM25 >= dense:", hk(F, "bm25", 1) >= hk(F, "dense", 1))
print("P4 hit@3 over Q1-Q8: BM25", hk(G["answerable_Q1_Q8"], "bm25", 3), "/ 8 | dense", hk(G["answerable_Q1_Q8"], "dense", 3), "/ 8")
json.dump({"config": CONFIG, "chunks": len(CH), "results": {k: {kk: vv for kk, vv in v.items() if kk not in ("bm25", "dense")} for k, v in RES.items()}}, open("retrieval_results.json", "w", encoding="utf-8"), indent=2)
print("\nsaved retrieval_results.json")
