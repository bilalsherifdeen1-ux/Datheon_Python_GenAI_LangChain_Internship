import runpy, io, contextlib
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path("retrieve.py")
Q, RES, CH, pairs, hit = g["Q"], g["RES"], g["CH"], g["pairs"], g["hit"]
def prank(top, d, a): return next((r for r, ci in enumerate(top, 1) if hit(ci, d, a)), None)
def drank(top, d): return next((r for r, ci in enumerate(top, 1) if CH[ci][0] == d), None)
print("EXPLORATORY diagnostics (not pre-registered). rank = position in the top 10; None = not in the top 10")
_ = [print(q["id"], q["type"], "|", d, "|", a[:30], "| passage rank BM25/dense:", prank(RES[q["id"]]["bm25"], d, a), prank(RES[q["id"]]["dense"], d, a), "| document rank BM25/dense:", drank(RES[q["id"]]["bm25"], d), drank(RES[q["id"]]["dense"], d)) for q in Q if q["answerable"] for d, a in pairs(q)]
