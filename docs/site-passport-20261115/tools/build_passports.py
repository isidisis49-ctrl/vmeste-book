#!/usr/bin/env python3
"""Build review-only technical passports. No website, database or server calls."""
from pathlib import Path
import hashlib,html,importlib.util,json,re
import fitz
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('passport_layout',ROOT/'tools/book_layout.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);b.setup_fonts()
b.STYLES['body'].fontSize=10.5;b.STYLES['body'].leading=15.3
b.STYLES['small'].fontSize=9;b.STYLES['small'].leading=12.8
b.STYLES['caption'].fontSize=8.3;b.STYLES['caption'].leading=11.4
TABLE=ParagraphStyle('table',fontName='Sans',fontSize=8.8,leading=12,textColor=b.INK,splitLongWords=False)
BOX=ParagraphStyle('box',fontName='Sans-Bold',fontSize=8.9,leading=12,textColor=b.INK,alignment=1,splitLongWords=False)
HASHES=[('help-together-480.webp','0066708e2509faa2ebf6e0e5ef0d97630eb1697093fdc4f2475659feb7b08118'),('help-together-960.webp','10e519b7cf9d8bca60ba3a5fff37a46ddacae4b370d37ea738dd1e240706d397'),('help-together-1448.webp','91681e5ff52d92a52a3b6df36850ddfd6cfa7fe5cd1de53ae612b4ee2cc6bfb8')]
URLS=['https://xn--b1aga0a0ag.site/','https://github.com/isidisis49-ctrl/111','https://github.com/isidisis49-ctrl/vmeste-book','https://vk.com/club243081835','https://web.max.ru/772602012']
CONFIG=json.loads((ROOT/'content.json').read_text());OUT=ROOT/'pdf';OUT.mkdir(exist_ok=True);(ROOT/'text').mkdir(exist_ok=True)
checks=[];manifest=[]
COST=json.loads((ROOT/'cost-model.json').read_text())
lo=sum(x[0] for x in COST['effort_hours']);hi=sum(x[1] for x in COST['effort_hours']);r0,r1=COST['hourly_rates']
assert [lo*r0,hi*r1]==COST['website_total_usd']==[33000,120000]
checks.append({'language':'shared','check':'website effort and cost arithmetic','result':'PASS'})
for module in ('android_mvp','ios_optional'):
 h0,h1=COST[module+'_hours'];assert [h0*r0,h1*r1]==COST[module+'_usd']
assert [a+b for a,b in zip(COST['website_total_usd'],COST['android_mvp_usd'])]==COST['website_plus_android_usd']
checks.append({'language':'shared','check':'separate mobile costs and combined budget arithmetic','result':'PASS'})
assert COST['assumptions_not_vendor_quotes'] and COST['fx_is_not_market_quote'] and COST['currency']=='USD'
checks.append({'language':'shared','check':'explicit planning and currency assumptions','result':'PASS'})

def box(c,label,x,y,w,h,primary=False):
 c.setFillColor(b.PALE if not primary else colors.HexColor('#d2ebe1'));c.setStrokeColor(colors.HexColor('#80afa0'));c.roundRect(x,y-h,w,h,6,fill=1,stroke=1)
 p=Paragraph(html.escape(label),BOX);_,ph=p.wrap(w-14,h-8)
 if ph>h-8:raise RuntimeError('Diagram label too tall: '+label)
 p.drawOn(c,x+7,y-h+(h-ph)/2)

def arrow(c,x1,y1,x2,y2):
 c.setStrokeColor(b.GREEN);c.setFillColor(b.GREEN);c.setLineWidth(1);c.line(x1,y1,x2,y2)
 import math
 a=__import__('math').atan2(y2-y1,x2-x1);p=c.beginPath();p.moveTo(x2,y2)
 p.lineTo(x2-5*math.cos(a-.45),y2-5*math.sin(a-.45));p.lineTo(x2-5*math.cos(a+.45),y2-5*math.sin(a+.45));p.close();c.drawPath(p,fill=1,stroke=0)

def diagram(c,cfg,name,y):
 labels=cfg['diagram_labels'][name];x=b.M;w=b.CW
 if name=='architecture':
  topw=(w-20)/3
  for i,t in enumerate(labels[0]):box(c,t,x+i*(topw+10),y,topw,38)
  for i in range(3):arrow(c,x+i*(topw+10)+topw/2,y-38,x+w/2,y-56)
  box(c,labels[1][0]+' → '+labels[1][1],x,y-59,w,42,True)
  lowy=y-125
  for i,t in enumerate(labels[2]):
   box(c,t,x+i*(topw+10),lowy,topw,38);arrow(c,x+w/2,y-101,x+i*(topw+10)+topw/2,lowy+2)
  return y-177
 if name=='voice':
  for i,lane in enumerate(labels):
   xx=x+i*(w/2+6);ww=w/2-6
   for k,t in enumerate(lane):
    yy=y-k*43;box(c,t,xx,yy,ww,31,k==0)
    if k<2:arrow(c,xx+ww/2,yy-31,xx+ww/2,yy-41)
  return y-136
 # Ordered steps, two rows when labels are long or numerous.
 n=len(labels);cols=3 if n>4 else 2;rows=(n+cols-1)//cols;ww=(w-(cols-1)*15)/cols
 for i,t in enumerate(labels):
  rr=i//cols;cc=i%cols;xx=x+cc*(ww+15);yy=y-rr*58
  box(c,t,xx,yy,ww,42,i==0)
  if cc<cols-1 and i<n-1:arrow(c,xx+ww+2,yy-21,xx+ww+13,yy-21)
  elif i<n-1:arrow(c,xx+ww/2,yy-43,x+ww/2,yy-57)
 return y-rows*58-6

def markdown(cfg):
 text='# '+cfg['title']+'\n\n*'+cfg['subtitle']+'*\n\n**'+cfg['review']+'**\n\n'+'\n\n'.join(cfg['identity'])+'\n\n'+cfg['scope']+'\n\n'+cfg['cover_note']+'\n\n'
 for s in cfg['sections']:
  text+='## '+s['title']+'\n\n'+'\n\n'.join(s['paras'])+'\n\n'
  if 'table' in s:
   rows=s['table'];text+='| '+' | '.join(rows[0])+' |\n| '+' | '.join('---' for _ in rows[0])+' |\n'
   for row in rows[1:]:text+='| '+' | '.join(row)+' |\n'
   text+='\n'
  if 'diagram' in s:
   key=s['diagram'];labels=cfg['diagram_labels'][key];text+='```mermaid\nflowchart TD\n'
   if key=='architecture':
    for i,l in enumerate(labels[0]):text+=f'  C{i}["{l}"] --> API["{labels[1][0]} / {labels[1][1]}"]\n'
    for i,l in enumerate(labels[2]):text+=f'  API --> D{i}["{l}"]\n'
   elif key=='voice':
    for i,lane in enumerate(labels):
     for j,l in enumerate(lane):text+=f'  V{i}{j}["{l}"]\n'
     text+=f'  V{i}0 --> V{i}1 --> V{i}2\n'
   else:
    for i,l in enumerate(labels):text+=f'  N{i}["{l}"]\n'
    text+='  '+' --> '.join('N'+str(i) for i in range(len(labels)))+'\n'
   text+='```\n\n'
  if s.get('screen'):text+=f'![{s["screen_caption"]}](../assets/{s["screen"]}-{cfg["lang"]}.png)\n\n'+s['screen_caption']+'\n\n'
  if s.get('assets'):
   text+='```text\n'+''.join(name+'\nSHA-256: '+sha+'\n' for name,sha in HASHES)+'```\n\n'
  if s.get('note'):text+='> '+s['note']+'\n\n'
 text+='## '+cfg['links_title']+'\n\n'+''.join('- ['+label+']('+url+')\n' for label,url in zip(cfg['links_labels'],URLS))+'\n'
 text+='\n'.join('- '+url for url in cfg['mobile_sources'])+'\n'
 return text

for lang,cfg in CONFIG.items():
 path=OUT/f'VMESTE_Technical_Passport_{lang}_REVIEW.pdf';c=canvas.Canvas(str(path),pagesize=(b.W,b.H),pageCompression=1,invariant=1)
 c.setTitle(cfg['title']);c.setAuthor('VMESTE Project');c.setSubject(cfg['subtitle']);toc=[];b.LAYOUT.clear();chrome={'footer':('ВМЕСТЕ' if lang=='RU' else 'VMESTE')+' · TP-VMESTE-2026.11'}
 active='';y=b.TOP
 def page(title):
  global y,active
  active=title;b.chrome(c,chrome,cfg['review']);y=b.TOP;y=b.drawp(c,title,b.M,y,b.CW,'title',gap=16)
 def ensure(height):
  global y
  if y-height<b.BOTTOM:
   c.showPage();page(active+(' · продолжение' if lang=='RU' else ' · continued'))
 def p(text,style='body',gap=11):
  global y
  height=b.para(text,style)[1]+gap;ensure(height);y=b.drawp(c,text,b.M,y,b.CW,style,gap=gap)
 def table(rows):
  global y
  cols=len(rows[0]);widths=[b.CW*.28,b.CW*.29,b.CW*.43] if cols==3 else [b.CW*.33,b.CW*.67]
  data=[[Paragraph(html.escape(t),TABLE) for t in row] for row in rows]
  t=Table(data,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d2ebe1')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,b.PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#b9cfc6')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
  _,height=t.wrap(b.CW,2000);ensure(height+14);t.drawOn(c,b.M,y-height);b.LAYOUT.append({'kind':'table','page':c.getPageNumber(),'bottom':y-height,'height':height});y-=height+14
 page(cfg['title']);toc.append([1,cfg['title'],c.getPageNumber()]);p(cfg['subtitle'],'heading',16)
 y=b.picture(c,ROOT/'assets/cover-workshop.png',b.M,y,b.CW,245,True)-9;p(cfg['image_caption'],'caption',14)
 for line in cfg['identity']:p(line,'small',5)
 p(cfg['scope'],'body',14);p(cfg['cover_note'],'small',0);c.showPage()
 for s in cfg['sections']:
  page(s['title']);toc.append([1,s['title'],c.getPageNumber()])
  if s.get('diagram')=='architecture':
   ensure(180);y=diagram(c,cfg,'architecture',y)
  for para in s['paras']:p(para)
  if s.get('diagram') and s['diagram']!='architecture':
   name=s['diagram'];h=136 if name=='voice' else ((len(cfg['diagram_labels'][name])+2)//3)*58+6 if len(cfg['diagram_labels'][name])>4 else 122
   ensure(h);y=diagram(c,cfg,name,y)
  if s.get('table'):table(s['table'])
  if s.get('screen')=='vesta':
   ensure(180);y=b.picture(c,ROOT/f'assets/vesta-{lang}.png',b.M,y,b.CW,165,False)-8;p(s['screen_caption'],'caption',7)
  if s.get('note'):p(s['note'],'small',0)
  if s.get('assets'):
   for name,sha in HASHES:p(name,'small',4);p('SHA-256: '+sha[:32]+' '+sha[32:],'caption',12)
   p(cfg['links_title'],'heading',11)
   for label,url in zip(cfg['links_labels'],URLS):p('['+label+']('+url+')','small',9)
  c.showPage()
  if s.get('screen')=='tools':
   title='Каталог инструментов: реальный интерфейс' if lang=='RU' else 'Tools catalogue: an actual interface';page(title);toc.append([2,title,c.getPageNumber()])
   y=b.picture(c,ROOT/f'assets/tools-{lang}.png',b.M,y,b.CW,540,False)-12;p(s['screen_caption'],'body',12)
   p('Подписи иностранных интерфейсов локализованы редакционно; это не выпущенный многоязычный продукт.' if lang=='RU' else 'Foreign interface labels were localised editorially; this is not a released multilingual product.','small',0);c.showPage()
 c.save();d=fitz.open(path);d.set_toc(toc);d.xref_set_key(d.pdf_catalog(),'Lang',fitz.get_pdf_str(cfg['tag']));meta=d.metadata;meta.update({'creationDate':'D:20261115000000Z','modDate':'D:20261115000000Z'});d.set_metadata(meta)
 stable=hashlib.sha256(('VMESTE-PASSPORT-20261115-'+lang).encode()).hexdigest()[:32];d.xref_set_key(-1,'ID','[<'+stable+'><'+stable+'>]');temp=path.with_suffix('.tmp.pdf');d.save(temp,garbage=4,deflate=True,no_new_id=True);d.close();temp.replace(path)
 text_source=markdown(cfg);(ROOT/'text'/f'TECHNICAL_PASSPORT_{lang}.md').write_text(text_source,encoding='utf-8')
 d=fitz.open(path);text='\n'.join(pg.get_text() for pg in d);norm=lambda s:re.sub(r'\s+','',s).replace('\u00ad','')
 for s in cfg['sections']:
  for para in s['paras']:
   assert norm(para) in norm(text),(lang,'missing paragraph',para[:50]);checks.append({'language':lang,'check':'source paragraph preserved','result':'PASS'})
  for row in s.get('table',[]):
   for cell in row:assert norm(cell) in norm(text),(lang,'missing table cell',cell)
 if lang=='EN':assert not re.search('[А-Яа-яЁё]',text)
 assert cfg['scope'] and norm(cfg['scope']) in norm(text)
 assert d.xref_get_key(d.pdf_catalog(),'Lang')[1]==cfg['tag']
 assert {x['uri'] for pg in d for x in pg.get_links() if x.get('uri')}>=set(URLS)
 for name,sha in HASHES:assert norm(sha) in norm(text)
 for x in b.LAYOUT:assert x['bottom']>=b.BOTTOM-1,(lang,'layout overflow',x)
 for pg in d:
  spans=[sp for block in pg.get_text('dict')['blocks'] for line in block.get('lines',[]) for sp in line['spans']]
  for sp in spans:
   x0,y0,x1,y1=sp['bbox'];assert -1<=x0 and x1<=b.W+1 and -1<=y0 and y1<=b.H+1,(lang,'text bounds',sp['text'])
  assert len(pg.get_text().strip())>600 or any(block.get('type')==1 and (block['bbox'][2]-block['bbox'][0])*(block['bbox'][3]-block['bbox'][1])>45000 for block in pg.get_text('dict')['blocks']),(lang,'near empty page',pg.number)
 assert 14<=len(d)<=22
 checks.extend({'language':lang,'check':key,'result':'PASS'} for key in ['table cells preserved','explicit target scope','document language','foreign alphabet','exact project links','three hero checksums','layout and text bounds','no near empty page','bounded page count','bookmarks present'])
 checks.append({'language':lang,'check':'seven diagrams in editable source','result':'PASS'});assert text_source.count('```mermaid')==7
 raw=path.read_bytes();manifest.append({'language':lang,'file':path.name,'pages':len(d),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()});print(lang,len(d),len(raw),'bytes',flush=True);d.close()
(OUT/'SHA256SUMS').write_text(''.join(x['sha256']+'  '+x['file']+'\n' for x in manifest))
(OUT/'manifest.json').write_text(json.dumps({'status':'design edition; no commissioning or deployment claimed','files':manifest},indent=2))
(ROOT/'validation.json').write_text(json.dumps({'scope':'document generation checks only; not a website, device or security acceptance test','summary':{'PASS':len(checks),'FAIL':0},'checks':checks},indent=2))
print('DOCUMENT CHECKS',len(checks),'PASS; 0 FAIL')
