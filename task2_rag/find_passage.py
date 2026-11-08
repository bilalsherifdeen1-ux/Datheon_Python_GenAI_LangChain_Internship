import json, sys
RAW = {k: " ".join(v["paragraphs"]) for k, v in json.load(open("data/corpus_clean.json", encoding="utf-8")).items()}
W = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 250
_ = [print("[" + k + "]", "...", t[max(0, i - N): i + N], "...\n") for k, t in RAW.items() for i in [t.lower().find(W.lower())] if i >= 0]
