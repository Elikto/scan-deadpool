#!/usr/bin/env python3
"""Collecte les notices Deadpool de la BnF SRU sans modifier les éditions existantes."""
import json,re,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
NS={'s':'http://www.loc.gov/zing/srw/','d':'http://purl.org/dc/elements/1.1/'}
OUT=Path(__file__).resolve().parents[1]/'data/bnf-deadpool.json'
def fields(node,key):
    return [x.text.strip() for x in node.findall('.//d:'+key,NS) if x.text and x.text.strip()]
def isbn(text):
    for raw in re.findall(r'97[89][0-9 -]{10,22}',text):
        n=re.sub(r'\D','',raw)
        if len(n)==13 and sum(int(c)*(1 if i%2==0 else 3) for i,c in enumerate(n))%10==0:return n
    return ''

def cover_for_title(title, number):
    """N'associe une image Google Books que si l'ISBN ou le titre concorde."""
    import difflib, unicodedata
    def norm(value):
        value=unicodedata.normalize('NFKD',str(value)).encode('ascii','ignore').decode().lower()
        return re.sub(r'[^a-z0-9]+',' ',value).strip()
    target=title.split(' / ')[0].split(' ; ')[0].strip()
    query='isbn:'+number if number else 'intitle:'+target[:110]
    try:
        params=urllib.parse.urlencode({'q':query,'maxResults':5,'langRestrict':'fr'})
        req=urllib.request.Request('https://www.googleapis.com/books/v1/volumes?'+params,headers={'User-Agent':'DeadpoolVF-Catalog/1.0'})
        with urllib.request.urlopen(req,timeout=8) as resp: data=json.load(resp)
        for volume in data.get('items',[]):
            info=volume.get('volumeInfo',{})
            candidate=norm(info.get('title','')+' '+info.get('subtitle',''))
            if 'deadpool' not in candidate:continue
            if difflib.SequenceMatcher(None,norm(target),candidate).ratio()<0.9:continue
            if number and number not in [str(x.get('identifier','')) for x in info.get('industryIdentifiers',[])]:continue
            cover=info.get('imageLinks',{}).get('thumbnail') or info.get('imageLinks',{}).get('smallThumbnail')
            if cover and cover.startswith(('http://','https://')):return cover.replace('http://','https://',1)
    except Exception:pass
    return ''

def collect():
    found={}
    for query in ('bib.title all "deadpool"','bib.anywhere all "deadpool"'):
        start=1
        while start<=3000:
            args=urllib.parse.urlencode({'version':'1.2','operation':'searchRetrieve','query':query,'recordSchema':'dublincore','startRecord':start,'maximumRecords':100})
            req=urllib.request.Request('https://catalogue.bnf.fr/api/SRU?'+args,headers={'User-Agent':'DeadpoolVF-Catalog/1.0'})
            with urllib.request.urlopen(req,timeout=35) as response: root=ET.fromstring(response.read())
            count=int(root.findtext('s:numberOfRecords','0',NS))
            records=root.findall('.//s:record',NS)
            for record in records:
                data=record.find('s:recordData',NS)
                if data is None:continue
                titles=fields(data,'title');descs=fields(data,'description')
                if not any('deadpool' in t.lower() for t in titles+descs):continue
                ids=fields(data,'identifier')
                ark=next((x for x in ids if 'ark:/12148/' in x),'')
                number=next((v for x in ids if (v:=isbn(x))),'')
                key=ark or number or '|'.join(titles)
                if not key:continue
                found[key]={'title':titles[0] if titles else '', 'isbn':number,'publisher':fields(data,'publisher'),'dates':fields(data,'date'),'language':fields(data,'language'),'type':fields(data,'type'),'bnf_url':ark,'identifiers':ids,'status':'Notice BnF : rapprochement édition à vérifier'}
            start+=len(records)
            if not records or start>count:break
    return sorted(found.values(),key=lambda x:(x['dates'][:1],x['title']))
if __name__=='__main__':
    try: books=collect()
    except Exception as exc:
        print('BnF indisponible :',exc)
        if OUT.exists():raise SystemExit(0)
        raise SystemExit(1)
    old={}
    if OUT.exists():
        try: old={x.get('bnf_url'):x for x in json.loads(OUT.read_text(encoding='utf-8')).get('books',[])}
        except (OSError,ValueError):pass
    # Maximum 30 requêtes par passage, conserver les images déjà validées.
    pending=0
    for book in books:
        book['cover']=old.get(book['bnf_url'],{}).get('cover','')
        if not book['cover'] and pending<30 and 'texte' in ' '.join(book['type']).lower():
            book['cover']=cover_for_title(book['title'],book['isbn'])
            pending+=1
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(),'source':'BnF SRU Dublin Core','books':books},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('BnF :',len(books),'notices candidates')
