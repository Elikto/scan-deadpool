#!/usr/bin/env python3
"""Complète les couvertures depuis des fiches Bédéthèque identifiées par ISBN.
Pas de recherche approximative, pas de téléchargement ni copie des images.
"""
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'data/books.json'
MATCHES=ROOT/'data/bedetheque-matches.json'
class Images(HTMLParser):
    def __init__(self):
        super().__init__();self.images=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('property') in ('og:image','og:image:secure_url') and a.get('content'):
            self.images.append(a['content'])
def main():
    data=json.loads(CATALOG.read_text(encoding='utf-8'))
    matches=json.loads(MATCHES.read_text(encoding='utf-8'))
    count=0
    for book in data['books']:
        isbn=re.sub(r'\D','',book.get('isbn') or '')
        page=matches.get(isbn)
        if not isbn or not page or book.get('cover'):continue
        if not re.fullmatch(r'https://www\.bedetheque\.com/BD-[\w%-]+\.html',page):continue
        try:
            req=urllib.request.Request(page,headers={'User-Agent':'DeadpoolVF-Catalog/1.0'})
            with urllib.request.urlopen(req,timeout=15) as response:
                html=response.read(1500000).decode('utf-8','replace')
            if isbn not in re.sub(r'[\s-]','',html):
                print('ISBN non confirmé dans la fiche:',isbn);continue
            parser=Images();parser.feed(html)
            image=next((x for x in parser.images if x.startswith('https://')),None)
            if image:
                book['cover']=image
                book['cover_source']=page
                count+=1
        except Exception as exc:print('Bédéthèque inaccessible:',isbn,exc)
    CATALOG.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Couvertures Bédéthèque associées:',count)
if __name__=='__main__':main()
