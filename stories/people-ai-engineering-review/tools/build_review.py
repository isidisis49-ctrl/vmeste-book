#!/usr/bin/env python3
"""Build separate review editions. Does not alter published books or issue releases.
Run from a repository checkout; dependencies are in tools/requirements-pdf.txt.
"""
from pathlib import Path
import argparse,hashlib,html,importlib.util,json,re
import fitz
from reportlab.pdfgen import canvas
from reportlab.lib import colors

HERE=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--repository',type=Path);args=parser.parse_args()
ROOT=args.repository or HERE.parents[1]
spec=importlib.util.spec_from_file_location('book_layout',ROOT/'tools/build_pdfs.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);b.setup_fonts(); b.STYLES['body'].fontSize=11.4; b.STYLES['body'].leading=17.4
CONFIG=json.loads((HERE/'editions.json').read_text())
OUT=HERE/'pdf';OUT.mkdir(exist_ok=True)
URLS=['https://xn--b1aga0a0ag.site/','https://github.com/isidisis49-ctrl/vmeste-book','https://vk.com/club243081835','https://web.max.ru/772602012','https://t.me/VmesteSiteBot','https://www.tbank-online.com/mybank/poolmoney/for/r_YlAHUiuafH.pMxtweDzlU/QV8J770476/']
results=[];checks=[]
for lang,cfg in CONFIG.items():
 old=json.loads((ROOT/'books/editions.json').read_text())[lang]
 source='# '+cfg['title']+'\n\n*'+cfg['subtitle']+'*\n\n'+cfg['intro']+'\n\n> '+cfg['status']+'\n\n'
 for heading,art,body in cfg['chapters']:source+='## '+heading+'\n\n'+body+'\n\n'
 source+='## '+cfg['links_title']+'\n\n'+cfg['closing']+'\n\n'
 for label,url in zip(cfg['link_labels'],URLS):source+='- ['+label+']('+url+')\n'
 source+='\n'+cfg['links_note']+'\n'
 (HERE/'text'/f'BOOK_{lang}.md').write_text(source,encoding='utf-8')
 article='# '+cfg['chapters'][4][0]+'\n\n*'+cfg['subtitle']+'*\n\n> '+cfg['status']+'\n\n'
 for heading,art,body in cfg['chapters'][4:]:article+='## '+heading+'\n\n'+body+'\n\n'
 article+='## '+cfg['links_title']+'\n\n'
 for label,url in zip(cfg['link_labels'],URLS):article+='- ['+label+']('+url+')\n'
 article+='\n'+cfg['links_note']+'\n'
 (HERE/'articles').mkdir(exist_ok=True)
 (HERE/'articles'/f'AI_ENTERPRISES_{lang}.md').write_text(article,encoding='utf-8')
 chrome={**old,'footer':('ВМЕСТЕ' if lang=='RU' else 'VMESTE')+' · '+cfg['review']}
 path=OUT/f'VMESTE_People_AI_Engineering_{lang}_REVIEW.pdf'
 c=canvas.Canvas(str(path),pagesize=(b.W,b.H),pageCompression=1,invariant=1)
 c.setTitle(cfg['title']);c.setAuthor(old['author']);c.setSubject(cfg['subtitle'])
 b.LAYOUT.clear();toc=[]
 b.chrome(c,chrome,cfg['review']);toc.append([1,cfg['title'],1]);y=b.TOP
 y=b.drawp(c,cfg['title'],b.M,y,b.CW,'title',gap=13)
 y=b.drawp(c,cfg['subtitle'],b.M,y,b.CW,'body',gap=18)
 y=b.picture(c,ROOT/'assets/art/cover-workshop.png',b.M,y,b.CW,335,True)-8
 y=b.drawp(c,cfg['ai_caption'],b.M,y,b.CW,'caption',gap=18)
 y=b.drawp(c,cfg['intro'],b.M,y,b.CW,'body',gap=20)
 y=b.drawp(c,cfg['status'],b.M,y,b.CW,'small',gap=12)
 c.showPage()
 for heading,art,body in cfg['chapters']:
  b.chrome(c,chrome,cfg['subtitle']);toc.append([1,heading,c.getPageNumber()]);y=b.TOP
  y=b.drawp(c,heading,b.M,y,b.CW,'heading',gap=14)
  paras=body.split('\n\n')
  needed=sum(b.para(t,'body')[1]+11 for t in paras)+b.para(cfg['ai_caption'],'caption')[1]+24
  imh=min(340 if art=='story' else 290,y-b.BOTTOM-needed)
  if imh<100:raise RuntimeError('Chapter too dense '+lang+' '+heading)
  source=ROOT/'assets/stories/est-k-komu-obratitsya-triptych.png' if art=='story' else ROOT/'assets/art'/f'{art}.png'
  y=b.picture(c,source,b.M,y,b.CW,imh,True)-8
  y=b.drawp(c,cfg['ai_caption'],b.M,y,b.CW,'caption',gap=14)
  for p in paras:y=b.drawp(c,p,b.M,y,b.CW,'body',gap=11)
  c.showPage()
 b.chrome(c,chrome,cfg['subtitle']);toc.append([1,cfg['screenshot_title'],c.getPageNumber()]);y=b.TOP
 y=b.drawp(c,cfg['screenshot_title'],b.M,y,b.CW,'title',gap=20)
 y=b.picture(c,ROOT/'assets/screens'/f'heating-{lang}.png',b.M,y,b.CW,390,False)-14
 y=b.drawp(c,cfg['screen_note'],b.M,y,b.CW,'body',gap=18)
 for note in old['heat_notes']:y=b.drawp(c,'• '+note,b.M,y,b.CW,'body',gap=11)
 y=b.drawp(c,old['status_text'],b.M,y,b.CW,'small',gap=12)
 c.showPage()
 b.chrome(c,chrome,cfg['review']);toc.append([1,cfg['links_title'],c.getPageNumber()]);y=b.TOP
 y=b.drawp(c,cfg['links_title'],b.M,y,b.CW,'title',gap=18)
 y=b.drawp(c,cfg['closing'],b.M,y,b.CW,'body',gap=18)
 for url,label in zip(URLS,cfg['link_labels']):
  h=43;c.setFillColor(b.PALE);c.roundRect(b.M,y-h,b.CW,h,6,fill=1,stroke=0)
  c.setFillColor(b.GREEN);c.setFont('Sans-Bold',11);c.drawString(b.M+14,y-24,label)
  c.linkURL(url,(b.M,y-h,b.W-b.M,y),relative=0,thickness=0);y-=h+10
 y=b.drawp(c,cfg['links_note'],b.M,y-8,b.CW,'small',gap=16)
 b.drawp(c,cfg['status'],b.M,y,b.CW,'caption',gap=0)
 c.showPage();c.save()
 doc=fitz.open(path);doc.xref_set_key(doc.pdf_catalog(),'Lang',fitz.get_pdf_str(old['tag']));doc.set_toc(toc)
 md=doc.metadata;md.update({'creationDate':'D:20261115000000Z','modDate':'D:20261115000000Z'});doc.set_metadata(md)
 stable=hashlib.sha256(('VMESTE-REVIEW-PEOPLE-AI-'+lang).encode()).hexdigest()[:32]
 doc.xref_set_key(-1,'ID','[<'+stable+'><'+stable+'>]')
 temp=path.with_suffix('.tmp.pdf');doc.save(temp,garbage=4,deflate=True,no_new_id=True);doc.close();temp.replace(path)
 d=fitz.open(path);text='\n'.join(p.get_text() for p in d)
 norm=lambda x:re.sub(r'\s+','',x).replace('\u00ad','')
 for heading,art,body in cfg['chapters']:
  for para in body.split('\n\n'):
   assert norm(para) in norm(text), (lang,'Missing body paragraph',para[:60])
   checks.append({'language':lang,'check':'paragraph preserved','result':'PASS'})
 assert len(d)==9
 assert len(d.get_toc())==9
 assert d.xref_get_key(d.pdf_catalog(),'Lang')[1]==old['tag']
 links={x['uri'] for p in d for x in p.get_links() if x.get('uri')}
 assert set(URLS)<=links
 if lang!='RU':assert not re.search('[А-Яа-яЁё]',text),(lang,'Cyrillic text found')
 for item in b.LAYOUT:
  assert item['bottom']>=b.BOTTOM-1,(lang,'Overflow',item)
 assert not re.search(r'\b(?:Dell|Oracle|Zabbix)\b|12 000|25 000',text,re.I)
 # Check text bounds, not just the layout records.
 for page in d:
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for span in line['spans']:
     x0,y0,x1,y1=span['bbox'];assert x0>=-1 and x1<=b.W+1 and y0>=-1 and y1<=b.H+1,(lang,'Text outside page',span['text'])
 checks.extend({'language':lang,'check':name,'result':'PASS'} for name in ['nine pages','nine bookmarks','PDF language','six exact links','page bounds','text layout bounds','no enterprise names or procurement details','language character check'])
 d.close();raw=path.read_bytes();results.append({'language':lang,'file':path.name,'pages':9,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
 print(lang,9,len(raw),'bytes',flush=True)
(OUT/'SHA256SUMS').write_text(''.join(f"{r['sha256']}  {r['file']}\n" for r in results))
(HERE/'validation.json').write_text(json.dumps({'scope':'PDF content, layout, links, language markers and redaction checks; not independent linguistic review','summary':{'PASS':len(checks),'FAIL':0},'checks':checks},ensure_ascii=False,indent=2))
(OUT/'manifest.json').write_text(json.dumps({'status':'review only; no release created','files':results},ensure_ascii=False,indent=2))
print('PASS',len(checks),'FAIL',0)
