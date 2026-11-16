#!/usr/bin/env python3
"""Metadonnees et offres explicitement fournies, sans scraping ni prix inventes."""
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "index.html").read_text(encoding="utf-8")
match = re.search(r"const books=(\[.*?\]);books[.]forEach", html, re.S)
if not match:
    raise SystemExit("Catalogue introuvable dans index.html")
books = json.loads(match.group(1))
now = datetime.now(timezone.utc).isoformat(timespec="seconds")
result = {"checked_at": now, "books": {}, "source": "ISBN Open Library + offres autorisees"}
feeds = ROOT / "data" / "merchant-offers.json"
provided = json.loads(feeds.read_text(encoding="utf-8")) if feeds.exists() else {}
allowed = {"Fnac", "Cultura", "BDfugue", "E.Leclerc", "Amazon"}
for book in books:
    isbn = re.sub(r"[^0-9X]", "", book.get("isbn") or "")
    entry = {"isbn": isbn, "cover": None, "offers": []}
    if len(isbn) in (10, 13):
        url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
        try:
            request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DeadpoolVF-Catalog/1.0"})
            with urllib.request.urlopen(request, timeout=8) as response:
                if response.status == 200 and response.headers.get("Content-Type", "").startswith("image/"):
                    entry["cover"] = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        except Exception:
            pass
    for offer in provided.get(isbn, []):
        if not isinstance(offer, dict) or offer.get("store") not in allowed:
            continue
        price = offer.get("price")
        if not isinstance(price, (int, float)) or isinstance(price, bool) or price < 0:
            continue
        if offer.get("availability") not in ("en stock", "rupture confirmée", "inconnue"):
            continue
        url = offer.get("url", "")
        if not isinstance(url, str) or not url.startswith("https://"):
            continue
        checked = offer.get("checked")
        if not isinstance(checked, str):
            continue
        try:
            stamp = datetime.fromisoformat(checked.replace("Z", "+00:00"))
            if stamp.tzinfo is None or (datetime.now(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds() > 172800:
                continue
        except ValueError:
            continue
        entry["offers"].append({k: offer[k] for k in ("store", "price", "availability", "url", "checked")})
    result["books"][book["id"]] = entry
out = ROOT / "data" / "catalog-status.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Vérifié {len(books)} références, {sum(bool(v['cover']) for v in result['books'].values())} couvertures, {sum(len(v['offers']) for v in result['books'].values())} offres fraîches.")
