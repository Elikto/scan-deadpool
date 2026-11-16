#!/usr/bin/env python3
"""Fusionne les fiches vérifiées dans l'ordre de priorité demandé.
Les données fournisseurs sont importées dans data/providers/*.json, indexées par ISBN.
Ne crée jamais de correspondance approximative.
"""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROVIDERS=["bedetheque","bdfugue","panini","excalibur","fnac","cultura","amazon","leclerc","carrefour","bubble","bdgest","decitre","gibert","momox","babelio","auchan","furet","mollat","placedeslibraires","rakuten","cdiscount","livreshebdo","electre"]
FIELDS=('title','cover','publisher','collection','year','series','volume','pages','authors')
def isbn(value):return re.sub(r'\D','',str(value or ''))
def main():
    catalog=json.loads((ROOT/'data/books.json').read_text(encoding='utf-8'))
    known={isbn(b.get('isbn')) for b in catalog['books'] if isbn(b.get('isbn'))}
    google=ROOT/'data/google-books-details.json'
    merged=json.loads(google.read_text(encoding='utf-8')) if google.exists() else {}
    merged={key:dict(value) for key,value in merged.items() if key in known}
    for provider in reversed(PROVIDERS):
        path=ROOT/'data/providers'/f'{provider}.json'
        if not path.exists():continue
        records=json.loads(path.read_text(encoding='utf-8'))
        for rawkey,entry in records.items():
            key=isbn(rawkey)
            if key not in known or not isinstance(entry,dict):continue
            url=str(entry.get('url') or '')
            if not url.startswith('https://'):continue
            item=merged.setdefault(key,{})
            for field in FIELDS:
                value=entry.get(field)
                if value not in ('',None,[]):item[field]=value
            item['source_name']=provider.title()
            item['source_url']=url
    # Les données fournisseur sont prioritaires sur Google Books; la BnF reste le repli.\n    out=ROOT/'data/source-details.json'
    out.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Fiches enrichies par sources prioritaires:',len(merged))
if __name__=='__main__':main()
