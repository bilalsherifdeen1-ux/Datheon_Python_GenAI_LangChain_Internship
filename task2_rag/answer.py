import json, os, sys, runpy, io, contextlib, hashlib
from concurrent.futures import ThreadPoolExecutor
from google import genai
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
MODEL = "gemini-3.7-flash"
RULE = "Answer only using the supplied passages. If the passages do not contain the answer, explicitly state that the answer is not available in the provided material."
CONFIG = {"model": MODEL, "temperature": 0, "retriever": "dense (sentence-transformers/all-MiniLM-L6-v2), top 3 chunks", "rag_rule": RULE, "no_retrieval_prompt": "Answer the following question. Be concise.", "suffix": "Be concise."}
DRY = "--dry" in sys.argv
KEY = os.environ.get("GEMINI_API_KEY")
(KEY or DRY) or sys.exit("Set GEMINI_API_KEY first (or run with --dry to preview without any requests).")
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path("retrieve.py")
Q, CH, RES = g["Q"], g["CH"], g["RES"]
client = genai.Client(api_key=KEY or "dry-run")
CACHE_FILE = "/content/drive/MyDrive/datheon_answers_cache.json" if os.path.isdir("/content/drive/MyDrive") else "answers_cache.json"
CACHE = json.load(open(CACHE_FILE, encoding="utf-8")) if os.path.exists(CACHE_FILE) else {}
STATE = {"stop": DRY, "err": None, "calls": 0}
def passages(q): return "\n\n".join("[Passage %d | source: %s]\n%s" % (n, CH[ci][0], CH[ci][2]) for n, ci in enumerate(RES[q["id"]]["dense"][:3], 1))
def prompt(c, q): return (RULE + "\n\nPassages:\n" + passages(q) + "\n\nQuestion: " + q["question"] + "\n\nBe concise.") if c == "rag" else ("Answer the following question. Be concise.\n\nQuestion: " + q["question"])
def key(c, q): return hashlib.sha256((MODEL + "|" + c + "|" + prompt(c, q)).encode("utf-8")).hexdigest()
JOBS = [("rag", q) for q in Q] + [("norag", q) for q in Q if q["answerable"]] + [("norag", q) for q in Q if not q["answerable"]]
EX = ThreadPoolExecutor(1)
def gen(p): return client.models.generate_content(model=MODEL, contents=p, config={"temperature": 0}).text
gen_r = retry(retry=retry_if_exception(lambda e: getattr(e, "code", None) == 503), stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=5, max=60), reraise=True)(gen)
def safe(p): f = EX.submit(gen_r, p); e = f.exception(); return (None, e) if e else (f.result(), None)
def store(k, text): CACHE[k] = text; json.dump(CACHE, open(CACHE_FILE, "w", encoding="utf-8")); STATE["calls"] += 1; return text
def fetch(c, q): return CACHE[key(c, q)] if key(c, q) in CACHE else (None if STATE["stop"] else (lambda r: store(key(c, q), r[0]) if r[1] is None else (STATE.update(stop=True, err=str(r[1])[:300]) or None))(safe(prompt(c, q))))
PENDING = [(c, q["id"]) for c, q in JOBS if key(c, q) not in CACHE]
print("config:", json.dumps(CONFIG)); print("jobs:", len(JOBS), "| already cached:", len(JOBS) - len(PENDING), "| requests still needed:", len(PENDING), "| cache file:", CACHE_FILE)
DRY and (print("\n--- DRY RUN: preview of prompts, no requests made ---\n\n[RAG prompt, Q1]\n" + prompt("rag", Q[0]) + "\n\n[NO-RETRIEVAL prompt, Q1]\n" + prompt("norag", Q[0]) + "\n\n[RAG prompt, Q9]\n" + prompt("rag", next(q for q in Q if q["id"] == "Q9"))) or sys.exit(0))
OUT = {(c, q["id"]): fetch(c, q) for c, q in JOBS}
def line(q): return "\n".join(["=" * 8 + " " + q["id"] + " (" + q["type"] + ")", "Q: " + q["question"], "GOLD: " + (json.dumps(q.get("items") or q["anchors"]) if q["answerable"] else "none, so the right behaviour is to say the answer is not available"), "RAG sources: " + ", ".join(CH[i][0] for i in RES[q["id"]]["dense"][:3]), "RAG: " + str(OUT[("rag", q["id"])]), "NO-RETRIEVAL: " + str(OUT.get(("norag", q["id"])))])
_ = [print(line(q), "\n") for q in Q]
json.dump({"config": CONFIG, "complete": all(v is not None for v in OUT.values()), "items": [{"id": q["id"], "type": q["type"], "question": q["question"], "rag_sources": [[CH[i][0], CH[i][1]] for i in RES[q["id"]]["dense"][:3]], "rag_answer": OUT[("rag", q["id"])], "norag_answer": OUT.get(("norag", q["id"]))} for q in Q]}, open("answers.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("requests made this run:", STATE["calls"], "| saved answers.json | complete:", all(v is not None for v in OUT.values()))
STATE["err"] and print("STOPPED EARLY:", STATE["err"], "\nCompleted answers are cached; re-run this script later to finish the rest.")
