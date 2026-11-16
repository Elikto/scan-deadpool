#!/usr/bin/env python3
"""Enrichit le catalogue avec les couvertures officielles de la BnF (par ARK).
Source: https://api.bnf.fr/fr/api-service-couvertures-du-catalogue-general
"""
import concurrent.futures
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'data/books.json'
API='https://openapi.bnf.fr/couverture/image/image/recupererImage'
HEADERS={'User-Agent':'DeadpoolVF-Bibliography/1.1 (bibliographic covers)'}
def check(book):
    if book.get('cover'):return None
    token=book.get('id','').removeprefix('bnf-')
    if not token.startswith('cb'):return None
    ark='ark:/12148/'+token
    query=urllib.parse.urlencode({'idArk':ark,'couverture':1,'taille':'originale','largeur':400,'hauteur':600})
    url=API+'?'+query
    try:
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=16) as response:
            content_type=response.headers.get('Content-Type','').lower()
            if not content_type.startswith('image/'):return None
            sample=response.read(4096)
            if len(sample)<1500:return None
        return (book['id'],url)
    except (urllib.error.URLError,TimeoutError,OSError):return None
def main():
    data=json.loads(CATALOG.read_text(encoding='utf-8'))
    books=data.get('books',[])
    pending=[b for b in books if not b.get('cover')]
    print('BnF : vérification de',len(pending),'notices sans couverture',flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        matches=dict(x for x in pool.map(check,pending) if x)
    date=datetime.now(timezone.utc).date().isoformat()
    for book in books:
        if book['id'] in matches:
            book['cover']=matches[book['id']]
            book['cover_source']='Bibliothèque nationale de France'
            book['cover_retrieved_at']=date
    CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Nouvelles couvertures BnF:',len(matches),'Total:',sum(bool(b.get('cover')) for b in books),flush=True)
if __name__=='__main__':main()
