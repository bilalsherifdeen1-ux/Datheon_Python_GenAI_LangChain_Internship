import os, sys
from typing import Optional
from google import genai
from pydantic import BaseModel, Field
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
class LineItem(BaseModel): description: str; quantity: float; unit_price: float
class Invoice(BaseModel): invoice_number: Optional[str] = Field(None, description="Invoice id exactly as written"); invoice_date: Optional[str] = Field(None, description="Date in ISO format YYYY-MM-DD"); currency: Optional[str] = Field(None, description="ISO 4217 code such as USD; map $ to USD only if nothing suggests otherwise"); items: list[LineItem]; total: Optional[float] = Field(None, description="Grand total exactly as stated on the document, never recomputed")
PROMPT = "Extract the invoice fields. Use null if a field is absent. Interpret ambiguous numeric dates as day/month/year. Return the grand total exactly as stated on the document, never recomputed. Items are only purchased products or services; do not list discount, tax or shipping lines as items.\n\n"
def extract(text): return Invoice.model_validate_json(client.models.generate_content(model=MODEL, contents=PROMPT + text, config={"response_mime_type": "application/json", "response_schema": Invoice, "temperature": 0}).text)
def check(p): return None if p.total is None or not p.items else ("OK" if abs(sum(i.quantity * i.unit_price for i in p.items) - p.total) < 0.01 else "REVIEW: items sum " + str(round(sum(i.quantity * i.unit_price for i in p.items), 2)) + " vs total " + str(p.total))
if __name__ == "__main__": inv = extract(open(sys.argv[1], encoding="utf-8").read()); print(inv.model_dump_json(indent=2)); print("consistency:", check(inv))
