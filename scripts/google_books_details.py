#!/usr/bin/env python3
"""Complète automatiquement les fiches par l'API publique Google Books, ISBN exact.
Les fournisseurs spécialisés priment dans le rendu; aucune correspondance par titre seul.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data/books.json'
OUT=ROOT/'data/google-books-details.json'
def fetch(isbn):
    url='https://www.googleapis.com/books/v1/volumes?'+urllib.parse.urlencode({'q':'isbn:'+isbn,'maxResults':5,'country':'FR'})
    req=urllib.request.Request(url,headers={'User-Agent':'DeadpoolVF-Bibliography/1.2'})
    with urllib.request.urlopen(req,timeout=14) as res:return json.load(res)
def main():
    catalog=json.loads(CAT.read_text(encoding='utf-8'))
    previous=json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    details=dict(previous)
    tried=0
    for b in catalog['books']:
        isbn=re.sub(r'\D','',b.get('isbn') or '')
        if len(isbn)!=13 or isbn in details:continue
        try:
            response=fetch(isbn)
            for volume in response.get('items',[]):
                info=volume.get('volumeInfo',{})
                ids={re.sub(r'\D','',str(i.get('identifier',''))) for i in info.get('industryIdentifiers',[])}
                if isbn not in ids:continue
                if 'deadpool' not in (info.get('title','')+' '+info.get('subtitle','')).lower():continue
                cover=info.get('imageLinks',{}).get('medium') or info.get('imageLinks',{}).get('thumbnail') or ''
                date=info.get('publishedDate','')
                year=int(date[:4]) if re.match(r'^(19|20)\d{2}',date) else None
                details[isbn]={'title':info.get('title',''),'publisher':info.get('publisher',''),'year':year,'pages':info.get('pageCount'),'authors':', '.join(info.get('authors',[])),'cover':cover.replace('http://','https://',1) if cover.startswith('http://') else cover,'source_name':'Google Books','source_url':info.get('infoLink','')}
                break
        except Exception as exc:print('Google Books:',isbn,str(exc),flush=True)
        tried+=1
        time.sleep(.15)
    OUT.write_text(json.dumps(details,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Google Books requêtes:',tried,'fiches:',len(details),flush=True)
if __name__=='__main__':main()
