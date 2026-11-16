#!/usr/bin/env python3
"""Metadonnees et offres explicitement fournies, sans scraping ni prix inventes."""
import json
import re
import urllib.request
import urllib.parse
import unicodedata
import time
import difflib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "index.html").read_text(encoding="utf-8")
match = re.search(r"const books=(\[.*?\]);books[.]forEach", html, re.S)
if not match:
    raise SystemExit("Catalogue introuvable dans index.html")
books = json.loads(match.group(1))
now = datetime.now(timezone.utc).isoformat(timespec="seconds")
result = {"checked_at": now, "books": {}, "source": "Open Library + Google Books + offres autorisées"}
feeds = ROOT / "data" / "merchant-offers.json"
provided = json.loads(feeds.read_text(encoding="utf-8")) if feeds.exists() else {}
def normalized(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def google_cover(isbn, title):
    """Utilise une image uniquement si Google Books confirme le même ISBN et un titre Deadpool."""
    params = urllib.parse.urlencode({"q": "isbn:" + isbn, "maxResults": 3, "printType": "books"})
    url = "https://www.googleapis.com/books/v1/volumes?" + params
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DeadpoolVF-Catalog/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            ids = {str(x.get("identifier", "")) for x in info.get("industryIdentifiers", [])}
            candidate = normalized(info.get("title", "") + " " + info.get("subtitle", ""))
            if isbn not in ids or "deadpool" not in candidate:
                continue
            cover = info.get("imageLinks", {}).get("thumbnail") or info.get("imageLinks", {}).get("smallThumbnail")
            if cover and cover.startswith(("https://", "http://")):
                return cover.replace("http://", "https://", 1)
    except Exception:
        pass
    return None


def read_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "DeadpoolCatalogue/2.0"})
    with urllib.request.urlopen(req, timeout=9) as response:
        return json.load(response)

def valid_isbn(value):
    if len(value) == 13 and value.isdigit():
        return sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(value)) % 10 == 0
    return False

def crosscheck(book, isbn):
    """Compare ISBN et titre dans deux catalogues; ne devine jamais les ISBN manquants."""
    sources = []
    endpoints = [
        ("Open Library", "https://openlibrary.org/isbn/" + isbn + ".json"),
        ("Google Books", "https://www.googleapis.com/books/v1/volumes?" +
         urllib.parse.urlencode({"q": "isbn:" + isbn, "maxResults": 5}))
    ]
    for name, url in endpoints:
        try:
            data = read_json(url)
            if name == "Google Books":
                candidates = [x.get("volumeInfo", {}) for x in data.get("items", [])]
            else:
                candidates = [data]
            for item in candidates:
                title = item.get("title", "")
                ids = [str(x.get("identifier", "")) for x in item.get("industryIdentifiers", [])]
                if name == "Google Books" and isbn not in ids:
                    continue
                a, b = normalized(book.get("title", "")), normalized(title)
                if "deadpool" not in b or difflib.SequenceMatcher(None, a, b).ratio() < 0.9:
                    continue
                sources.append({"name": name, "url": url, "title": title,
                                "published_date": item.get("publishedDate") or item.get("publish_date")})
                break
        except Exception:
            continue
    return sources

allowed = {"Fnac", "Cultura", "BDfugue", "E.Leclerc", "Amazon"}
for book in books:
    isbn = re.sub(r"[^0-9X]", "", book.get("isbn") or "")
    entry = {"isbn": isbn, "cover": None, "offers": [], "bibliography": {"status": "non vérifié", "sources": []}}
    if valid_isbn(isbn):
        url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
        try:
            request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DeadpoolVF-Catalog/1.0"})
            with urllib.request.urlopen(request, timeout=8) as response:
                if response.status == 200 and response.headers.get("Content-Type", "").startswith("image/"):
                    entry["cover"] = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        except Exception:
            pass
    if valid_isbn(isbn) and not entry["cover"]:
        entry["cover"] = google_cover(isbn, book.get("title", ""))
        time.sleep(0.2)
    if valid_isbn(isbn):
        entry["bibliography"]["sources"] = crosscheck(book, isbn)
        if entry["bibliography"]["sources"]:
            entry["bibliography"]["status"] = "ISBN et titre concordants"
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
