#!/usr/bin/env python3
"""Collecte bibliographique prudente BnF SRU + Google Books. Python standard."""
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/books.json'
NS={'srw':'http://www.loc.gov/zing/srw/','dc':'http://purl.org/dc/elements/1.1/'}
HEADERS={'User-Agent':'DeadpoolVF-Bibliography/1.0 (public bibliographic catalog)'}
def fetch(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=25) as r:return r.read()
def strings(record,name):
    return [e.text.strip() for e in record.findall('.//dc:'+name,NS) if e.text and e.text.strip()]
def isbn13(values):
    for v in values:
        for candidate in re.findall(r'(?<!\d)97[89][\d -]{10,18}',v):
            number=re.sub(r'[^\d]','',candidate)[:13]
            if len(number)==13 and sum(int(x)*(1 if i%2==0 else 3) for i,x in enumerate(number))%10==0:return number
    return ''
def cover_by_isbn(isbn):
    if not isbn:return ''
    query=urllib.parse.urlencode({'q':'isbn:'+isbn,'maxResults':5})
    try:
        data=json.loads(fetch('https://www.googleapis.com/books/v1/volumes?'+query))
        for volume in data.get('items',[]):
            info=volume.get('volumeInfo',{})
            ids={str(x.get('identifier','')) for x in info.get('industryIdentifiers',[])}
            if isbn not in ids or 'deadpool' not in (info.get('title','')+' '+info.get('subtitle','')).lower():continue
            image=info.get('imageLinks',{}).get('thumbnail') or info.get('imageLinks',{}).get('smallThumbnail')
            if image and image.startswith(('https://','http://')):return image.replace('http://','https://',1)
    except Exception as exc:print('Couverture indisponible',isbn,str(exc))
    return ''
def openlibrary_cover(isbn):
    """Open Library renvoie 404 si l'ISBN n'a pas de couverture (default=false)."""
    if not isbn:return ''
    url='https://covers.openlibrary.org/b/isbn/'+urllib.parse.quote(isbn)+'-L.jpg?default=false'
    try:
        req=urllib.request.Request(url,headers={**HEADERS,'Range':'bytes=0-1023'})
        with urllib.request.urlopen(req,timeout=12) as response:
            kind=response.headers.get('Content-Type','')
            if response.status in (200,206) and kind.startswith('image/'):
                return url
    except Exception:pass
    return ''

def collect():
    found={}
    for start in range(1,402,100):
        query=urllib.parse.urlencode({'version':'1.2','operation':'searchRetrieve','query':'bib.title all "deadpool"','recordSchema':'dublincore','startRecord':start,'maximumRecords':100})
        root=ET.fromstring(fetch('https://catalogue.bnf.fr/api/SRU?'+query))
        records=root.findall('.//srw:record',NS)
        if not records:break
        for record in records:
            titles=strings(record,'title')
            if not titles or 'deadpool' not in titles[0].lower():continue
            types=' '.join(strings(record,'type')).lower()
            if types and not any(x in types for x in ('texte','text','livre','book','imprim')):continue
            identifiers=strings(record,'identifier')
            ark=next((x for x in identifiers if 'ark:/12148/' in x),'')
            match=re.search(r'ark:/12148/([a-zA-Z0-9]+)',ark)
            if not match:continue
            token=match.group(1)
            isbn=isbn13(identifiers)
            years=' '.join(strings(record,'date'))
            matchyear=re.search(r'\b(?:19|20)\d{2}\b',years)
            publisher='; '.join(strings(record,'publisher'))
            found[token]={'id':'bnf-'+token,'title':titles[0],'publisher':publisher,'collection':'','year':int(matchyear.group()) if matchyear else None,'isbn':isbn,'cover':'','source':'https://catalogue.bnf.fr/ark:/12148/'+token}
        if len(records)<100:break
        time.sleep(.5)
    return list(found.values())
def main():
    previous={}
    if OUT.exists():
        try:previous={b['id']:b for b in json.loads(OUT.read_text(encoding='utf-8')).get('books',[])}
        except (ValueError,KeyError):pass
    books=collect()
    # Respecter les couvertures vérifiées déjà trouvées.
    requests=0
    for b in books:
        old=previous.get(b['id'],{})
        if old.get('isbn')==b['isbn'] and old.get('cover'):b['cover']=old['cover']
        elif b['isbn'] and requests<100:
            b['cover']=cover_by_isbn(b['isbn']) or openlibrary_cover(b['isbn'])
            requests+=1
            time.sleep(.2)
    # Éviter les doublons exacts d'ISBN, conserver les éditions sans ISBN.
    unique=[];seen=set()
    for b in sorted(books,key=lambda b:(b['year'] or 0,b['title'])):
        key='isbn:'+b['isbn'] if b['isbn'] else b['id']
        if key in seen:continue
        seen.add(key);unique.append(b)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(),'books':unique},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Notices:',len(unique),'ISBN:',sum(bool(b['isbn']) for b in unique),'covers:',sum(bool(b['cover']) for b in unique))
if __name__=='__main__':main()
