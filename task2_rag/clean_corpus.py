import glob, re, json, os
def clean(t): L = t.splitlines(); b = [l.strip() for l in L[4:]]; i = b.index("References") if "References" in b else len(b); return L[:3], [l for l in b[:i] if l and not re.fullmatch(r"\(?\d+\)?\.?|\.", l)]
CORPUS = {os.path.basename(f)[:-4]: clean(open(f, encoding="utf-8").read()) for f in sorted(glob.glob("data/doc*.txt"))}
json.dump({k: {"source": h[0][8:], "accessed": h[2][14:], "paragraphs": b} for k, (h, b) in CORPUS.items()}, open("data/corpus_clean.json", "w", encoding="utf-8"))
_ = [print(k, "paragraphs:", len(b), "words:", sum(len(x.split()) for x in b)) for k, (h, b) in CORPUS.items()]
