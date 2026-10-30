import os, re, sys, json, time, hashlib, datetime
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
H = {"User-Agent": "Mozilla/5.0 (compatible; student-rag-project; local research use)"}
EX = ThreadPoolExecutor(1)
URLS = [l.split()[0] for l in open(sys.argv[1] if len(sys.argv) > 1 else "urls.txt", encoding="utf-8").read().splitlines() if l.strip() and not l.strip().startswith("#")]
os.makedirs("data", exist_ok=True)
def get(u): f = EX.submit(requests.get, u, headers=H, timeout=30); return None if f.exception() else f.result()
def text_of(html): s = BeautifulSoup(html, "html.parser"); [t.decompose() for t in s(["script", "style", "nav", "footer", "header", "aside", "form"])]; m = s.find("article") or s.find("main") or s.body or s; return (s.title.string.strip() if s.title and s.title.string else ""), "\n".join(l.strip() for l in m.get_text("\n").splitlines() if l.strip())
def process(i, u): time.sleep(2); r = get(u); ok = r is not None and r.status_code == 200; title, text = text_of(r.text) if ok else ("", ""); name = "doc%02d_%s.txt" % (i, re.sub(r"[^a-z0-9]+", "-", u.rstrip("/").split("/")[-1].lower()).strip("-")[:40]); ok and open(os.path.join("data", name), "w", encoding="utf-8").write("SOURCE: " + u + "\nFINAL_URL: " + r.url + "\nACCESSED_UTC: " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d") + "\n\n" + text); return {"id": i, "url": u, "status": "ERROR" if r is None else r.status_code, "final_url": r.url if r is not None else None, "title": title, "words": len(text.split()), "file": name if ok else None, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest() if ok else None}
ROWS = [process(i, u) for i, u in enumerate(URLS, 1)]
json.dump(ROWS, open("data/manifest.json", "w", encoding="utf-8"), indent=2)
_ = [print(r["id"], r["status"], r["words"], "THIN-CHECK" if r["status"] == 200 and r["words"] < 150 else "", "|", (r["title"] or "")[:60], "|", r["url"]) for r in ROWS]
print("fetched:", sum(1 for r in ROWS if r["file"]), "of", len(ROWS), "| manifest: data/manifest.json")
