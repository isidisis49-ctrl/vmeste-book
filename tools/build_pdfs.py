#!/usr/bin/env python3
"""Build four dense illustrated reading editions. Source artwork is never retouched.
Original PNGs are preserved; JPEG encoding is used only for PDF image streams.
"""
from __future__ import annotations
import argparse,hashlib,html,io,json,re
from pathlib import Path
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
import fitz

ROOT=Path(__file__).resolve().parents[1]
W,H=595.2756,841.8898
M=43;CW=W-2*M;TOP=H-76;BOTTOM=51
INK=colors.HexColor('#163b38');GREEN=colors.HexColor('#176553');GOLD=colors.HexColor('#b88031');MUTED=colors.HexColor('#596f6c');PALE=colors.HexColor('#edf5f1');PAPER=colors.HexColor('#fffdf8')
URLS=['https://xn--b1aga0a0ag.site/','https://github.com/isidisis49-ctrl/vmeste-book','https://t.me/VmesteSiteBot','https://vk.com/club243081835','https://web.max.ru/772602012','https://www.tbank-online.com/mybank/poolmoney/for/r_YlAHUiuafH.pMxtweDzlU/QV8J770476/']
ARTS=['community','local-ai','engineering','robotics','cover-workshop']
STYLES={};IMAGES={};LAYOUT=[]

def setup_fonts():
    base=Path('/usr/share/fonts/truetype/dejavu')
    for name,file in [('Sans','DejaVuSans.ttf'),('Sans-Bold','DejaVuSans-Bold.ttf'),('Serif','DejaVuSerif.ttf'),('Serif-Italic','DejaVuSerif-Italic.ttf')]:
        p=base/file
        if not p.exists():raise RuntimeError('Install fonts-dejavu-core; missing '+file)
        pdfmetrics.registerFont(TTFont(name,str(p)))
    pdfmetrics.registerFontFamily('Sans',normal='Sans',bold='Sans-Bold')
    pdfmetrics.registerFontFamily('Serif',normal='Serif',italic='Serif-Italic')
    common={'textColor':INK,'allowWidows':0,'allowOrphans':0,'splitLongWords':False}
    STYLES.update({
     'body':ParagraphStyle('body',fontName='Serif',fontSize=10.8,leading=16,spaceAfter=0,**common),
     'quote':ParagraphStyle('quote',fontName='Serif-Italic',fontSize=10.5,leading=15.4,textColor=GREEN,splitLongWords=False),
     'heading':ParagraphStyle('heading',fontName='Sans-Bold',fontSize=18,leading=22,**common),
     'title':ParagraphStyle('title',fontName='Sans-Bold',fontSize=22,leading=28,**common),
     'caption':ParagraphStyle('caption',fontName='Sans',fontSize=8.5,leading=12,textColor=MUTED,splitLongWords=False),
     'small':ParagraphStyle('small',fontName='Sans',fontSize=9.4,leading=14,textColor=MUTED,splitLongWords=False),
     'card':ParagraphStyle('card',fontName='Sans',fontSize=10.2,leading=15,textColor=INK,splitLongWords=False)
    })

def inline(text):
    links=[]
    def store(m):
        links.append('<link href="'+html.escape(m[2],quote=True)+'" color="#176553">'+html.escape(m[1])+'</link>');return '@@L'+str(len(links)-1)+'@@'
    text=re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)',store,text)
    text=html.escape(text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)',r'<i>\1</i>',text)
    for i,s in enumerate(links):text=text.replace('@@L'+str(i)+'@@',s)
    return text

def para(text,style,width=CW,raw=False):
    p=Paragraph(text if raw else inline(text),STYLES[style]);_,h=p.wrap(width,2000);return p,h

def drawp(c,text,x,y,width=CW,style='body',gap=9,raw=False):
    p,h=para(text,style,width,raw=raw)
    if y-h<BOTTOM-1:raise RuntimeError('PAGE_OVERFLOW '+str(c.getPageNumber())+' '+text[:70])
    p.drawOn(c,x,y-h);LAYOUT.append({'page':c.getPageNumber(),'kind':'text','bottom':round(y-h,2),'height':round(h,2),'style':style})
    return y-h-gap

def image_data(path,art=False):
    key=(str(path),art)
    if key not in IMAGES:
        if art:
            # Publication encoding only: no crop, paint, text replacement or pixel edit.
            with PILImage.open(path) as source:
                buffer=io.BytesIO();source.convert('RGB').save(buffer,format='JPEG',quality=92,optimize=True);buffer.seek(0);IMAGES[key]=ImageReader(buffer)
        else:IMAGES[key]=ImageReader(str(path))
    return IMAGES[key]

def picture(c,path,x,y,width=CW,maxheight=300,art=False):
    im=image_data(path,art);iw,ih=im.getSize();scale=min(width/iw,maxheight/ih);dw,dh=iw*scale,ih*scale
    xx=x+(width-dw)/2;c.drawImage(im,xx,y-dh,width=dw,height=dh,mask='auto')
    LAYOUT.append({'page':c.getPageNumber(),'kind':'image','bottom':round(y-dh,2),'height':round(dh,2),'width':round(dw,2)})
    return y-dh

def chrome(c,cfg,kicker):
    c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(GREEN);c.setFont('Sans-Bold',8);c.drawString(M,H-37,kicker.upper())
    c.setStrokeColor(colors.HexColor('#d6e4dd'));c.setLineWidth(.6);c.line(M,H-48,W-M,H-48)
    c.setFont('Sans',7.8);c.setFillColor(MUTED);c.drawString(M,29,cfg['footer']);c.drawRightString(W-M,29,f'{c.getPageNumber():02d}')
    c.linkURL(URLS[0],(M,21,M+175,40),relative=0,thickness=0)

def sections(path):
    src=path.read_text(encoding='utf-8');chunks=re.split(r'^## ',src,flags=re.M);head=chunks.pop(0).strip().split('\n\n')
    title=head[0].removeprefix('# ');subtitle=head[1].strip('*')
    parts=[]
    for chunk in chunks:
        heading,body=chunk.split('\n',1);parts.append({'heading':heading.strip(),'paras':[p.strip() for p in body.strip().split('\n\n') if p.strip()]})
    if len(parts)!=11:raise RuntimeError('EXPECTED_TEN_STORY_SECTIONS_PLUS_LINKS')
    return title,subtitle,parts

def quote(c,text,x,y,width=CW):
    p,h=para(text,'quote',width-22);c.setFillColor(PALE);c.roundRect(x,y-h-20,width,h+14,7,fill=1,stroke=0)
    p.drawOn(c,x+11,y-h-12);LAYOUT.append({'page':c.getPageNumber(),'kind':'text','bottom':round(y-h-12,2),'height':round(h,2),'style':'quote'})
    return y-h-30

def cover(c,cfg,title,subtitle,lang):
    c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(INK);c.rect(0,H-45,W,45,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('Sans-Bold',10);c.drawString(M,H-28,cfg['series']);c.drawRightString(W-M,H-28,lang)
    y=picture(c,ROOT/'assets/art/cover-workshop.png',0,H-45,W,420,True)-8
    y=drawp(c,cfg['image_type'],M,y,CW,'caption',gap=23)
    c.setFont('Sans-Bold',38);c.setFillColor(GREEN);c.drawString(M,y-38,'ВМЕСТЕ' if lang=='RU' else 'VMESTE');y-=60
    short=title.split(' — ',1)[-1]
    y=drawp(c,short,M,y,CW,'title',gap=15);y=drawp(c,subtitle,M,y,CW,'body',gap=20)
    y=drawp(c,cfg['topics'],M,y,CW,'small',gap=13)
    c.setStrokeColor(GOLD);c.setLineWidth(2);c.line(M,y,W-M,y);y-=23
    drawp(c,cfg['join'],M,y,CW,'body',gap=0)
    c.linkURL(URLS[1],(M,45,W-M,90),relative=0,thickness=0)
    c.setFont('Sans',8);c.setFillColor(MUTED);c.drawString(M,48,'github.com/isidisis49-ctrl/vmeste-book')
    c.showPage()

def narrative(c,cfg,parts,group):
    chrome(c,cfg,cfg['page_tags'][group]);chosen=parts[group*2:group*2+2]
    estimated=0
    for s in chosen:
        estimated+=para(s['heading'],'heading')[1]+12
        for t in s['paras']:
            if t.startswith('*') and t.endswith('*'):estimated+=para(t.strip('*'),'quote',CW-22)[1]+30
            else:estimated+=para(t,'body')[1]+11
    caph=para(cfg['art_captions'][group],'caption')[1]
    imageheight=min(267,TOP-BOTTOM-estimated-caph-31)
    if imageheight<145:raise RuntimeError('CHAPTER_PAGE_TOO_DENSE '+str(group))
    y=picture(c,ROOT/'assets/art'/f'{ARTS[group]}.png',M,TOP,CW,imageheight,True)-8
    y=drawp(c,cfg['art_captions'][group],M,y,CW,'caption',gap=18)
    for index,s in enumerate(chosen):
        y=drawp(c,s['heading'],M,y,CW,'heading',gap=10)
        for text in s['paras']:
            if text.startswith('*') and text.endswith('*'):y=quote(c,text.strip('*'),M,y)
            else:y=drawp(c,text,M,y,CW,'body',gap=11)
        if not index:y-=6
    c.showPage()

def box(c,cfg,y,texts,title=None):
    title=title or cfg['status_title'];elements=[(title,'heading')]+[(t,'card') for t in texts]
    h=sum(para(t,st,CW-30)[1]+10 for t,st in elements)+20
    if y-h<BOTTOM:raise RuntimeError('BOX_OVERFLOW')
    c.setFillColor(PALE);c.roundRect(M,y-h,CW,h,9,fill=1,stroke=0);yy=y-15
    for t,st in elements:yy=drawp(c,t,M+15,yy,CW-30,st,gap=10)
    return y-h-15

def documentary(c,cfg,lang,name):
    chrome(c,cfg,cfg['gallery']);prefix='heat' if name=='heating' else name
    y=drawp(c,cfg[prefix+'_title'],M,TOP,CW,'heading',gap=18)
    # Excerpts are actual browser captures. Keep their aspect ratios and all labels.
    heights={'vesta':350,'heating':330,'tools':470}
    y=picture(c,ROOT/'assets/screens'/f'{name}-{lang}.png',M,y,CW,heights[name],False)-10
    y=drawp(c,cfg[prefix+'_caption'],M,y,CW,'small',gap=16)
    if name=='tools':
        for note in cfg['tools_notes']:y=drawp(c,'• '+note,M,y,CW,'body',gap=10)
        y=drawp(c,cfg['locale_note'],M,y,CW,'caption',gap=0)
    else:
        y=box(c,cfg,y,cfg[prefix+'_notes'])
        y=drawp(c,cfg['locale_note'],M,y,CW,'caption',gap=10)
        if y-BOTTOM>60:drawp(c,cfg['status_text'],M,y,CW,'small',gap=0)
    c.showPage()

def contact(c,cfg,parts):
    chrome(c,cfg,cfg['join']);y=drawp(c,cfg['links_title'],M,TOP,CW,'title',gap=14)
    y=drawp(c,cfg['links_intro'],M,y,CW,'body',gap=15)
    hosts=['xn--b1aga0a0ag.site','github.com/isidisis49-ctrl/vmeste-book','t.me/VmesteSiteBot','vk.com/club243081835','web.max.ru/772602012','www.tbank-online.com']
    for i,(url,label) in enumerate(zip(URLS,cfg['link_labels'])):
        h=43;c.setFillColor(GREEN if i==5 else PALE);c.roundRect(M,y-h,CW,h,7,fill=1,stroke=0)
        c.setFont('Sans-Bold',11);c.setFillColor(colors.white if i==5 else INK);c.drawString(M+14,y-17,label)
        c.setFont('Sans',8);c.setFillColor(colors.HexColor('#e7f2ec') if i==5 else MUTED);c.drawString(M+14,y-31,hosts[i]);c.linkURL(url,(M,y-h,W-M,y),relative=0,thickness=0);y-=h+7
    y-=8;y=drawp(c,cfg['donation_note'],M,y,CW,'small',gap=12);y=drawp(c,cfg['channel_note'],M,y,CW,'caption',gap=17)
    # A compact visual closing, with the original source disclaimer retained.
    remaining=y-BOTTOM
    closing=cfg['closing'];ph=para(closing,'quote',CW*.46)[1]
    imageheight=min(135,remaining-15)
    if imageheight>75:
        picture(c,ROOT/'assets/art/community.png',M,y,CW*.5,imageheight,True)
        drawp(c,closing,M+CW*.54,y-10,CW*.46,'quote',gap=0)
    final=parts[-1]['paras'][-1]
    # The original closing is covered by the translated status notes, but retain it verbatim.
    if not final.startswith(('**','- ')):
        drawp(c,final,M,BOTTOM+24+para(final,'caption')[1],CW,'caption',gap=0)
    c.showPage()

def build(lang,cfg,out):
    title,subtitle,parts=sections(ROOT/f'books/BOOK_{lang}.md');path=out/f'VMESTE_Book_{lang}_2026.pdf'
    c=canvas.Canvas(str(path),pagesize=(W,H),pageCompression=1,invariant=1)
    c.setTitle(title);c.setAuthor(cfg['author']);c.setSubject(cfg['subject'])
    cover(c,cfg,title,subtitle,lang)
    for group in range(5):narrative(c,cfg,parts,group)
    for name in ['vesta','heating','tools']:documentary(c,cfg,lang,name)
    contact(c,cfg,parts);c.save()
    # Set an explicit document language and deterministic editorial date.
    d=fitz.open(path);catalog=d.pdf_catalog();d.xref_set_key(catalog,'Lang',fitz.get_pdf_str(cfg['tag']))
    meta=d.metadata;meta.update({'creationDate':'D:20261115000000Z','modDate':'D:20261115000000Z'});d.set_metadata(meta)
    toc=[[1,title,1]]+[[1,cfg['page_tags'][i],i+2] for i in range(5)]+[[1,cfg[k+'_title'],page] for k,page in [('vesta',7),('heat',8),('tools',9)]]+[[1,cfg['links_title'],10]]
    d.set_toc(toc);stable=hashlib.sha256(('VMESTE-2026-'+lang+title).encode()).hexdigest()[:32];d.xref_set_key(-1,'ID','[<'+stable+'><'+stable+'>]');tmp=path.with_suffix('.tmp.pdf');d.save(tmp,garbage=4,deflate=True,no_new_id=True);d.close();tmp.replace(path)
    print(lang,path.stat().st_size,'bytes',flush=True)
    return {'language':lang,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=ROOT/'downloads');a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
    setup_fonts();config=json.loads((ROOT/'books/editions.json').read_text());results=[]
    for lang in ['RU','EN','DE','FR']:
        LAYOUT.clear();results.append(build(lang,config[lang],a.output_dir));(a.output_dir/f'layout-{lang}.json').write_text(json.dumps(LAYOUT,indent=2))
    (a.output_dir/'SHA256SUMS').write_text(''.join(x['sha256']+'  '+x['file']+'\n' for x in results));(a.output_dir/'editions-manifest.json').write_text(json.dumps({'edition':'2026.11.15','files':results},indent=2))
if __name__=='__main__':main()
