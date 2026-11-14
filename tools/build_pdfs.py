#!/usr/bin/env python3
"""Build public PDF reading editions from the published multilingual markdown.
This script never reads the VMESTE application repository or private data.
"""
from pathlib import Path
import re, html, io
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether
import cairosvg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"downloads"
OUT.mkdir(exist_ok=True)
font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not Path(font).exists(): raise RuntimeError("DejaVu font missing on build runner")
pdfmetrics.registerFont(TTFont("DVS",font))
pdfmetrics.registerFont(TTFont("DVS-Bold",bold))
pdfmetrics.registerFontFamily("DVS",normal="DVS",bold="DVS-Bold")
INK=colors.HexColor("#12344D")
TEAL=colors.HexColor("#12686D")
LIGHT=colors.HexColor("#637C8F")
base=ParagraphStyle("body",fontName="DVS",fontSize=10.6,leading=17.5,textColor=INK,spaceAfter=10)
heading=ParagraphStyle("chapter",parent=base,fontName="DVS-Bold",fontSize=17.8,leading=25,textColor=TEAL,spaceBefore=5,spaceAfter=15,keepWithNext=True)
title=ParagraphStyle("title",parent=base,fontName="DVS-Bold",fontSize=24,leading=34,alignment=TA_CENTER,textColor=INK)
sub=ParagraphStyle("sub",parent=base,fontSize=11,leading=19,alignment=TA_CENTER,textColor=LIGHT)
small=ParagraphStyle("small",parent=base,fontSize=8,leading=13,textColor=LIGHT)
boldbody=ParagraphStyle("bold",parent=base,fontName="DVS-Bold")
ARTWORK = ["community", "ai", "tashi", "heat", "tools", "robot"]
def art(name="community", width=16.3*cm):
    source = ROOT/"assets"/"illustrations"/(name+".svg")
    data = cairosvg.svg2png(bytestring=source.read_bytes(), output_width=1350)
    im = Image(io.BytesIO(data))
    im.drawWidth = width
    im.drawHeight = width*360/900
    return im
def inline(text):
    # Convert Markdown links to ReportLab links without injecting untrusted tags.
    links=[]
    def store(m):
        label=html.escape(m.group(1))
        url=html.escape(m.group(2),quote=True)
        links.append(f'<link href="{url}" color="#12686D"><u>{label}</u></link>')
        return f"@@LINK{len(links)-1}@@"
    text=re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',store,text)
    text=html.escape(text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)',r'<i>\1</i>',text)
    for i,link in enumerate(links):text=text.replace(f"@@LINK{i}@@",link)
    return text
def footer(canv,doc):
    canv.saveState()
    w,h=A4
    canv.setStrokeColor(colors.HexColor("#D5E5E7"))
    canv.line(1.8*cm,1.55*cm,w-1.8*cm,1.55*cm)
    canv.setFont("DVS",8)
    canv.setFillColor(LIGHT)
    canv.drawString(1.8*cm,1.15*cm,"VMESTE  ·  vmeste.site")
    canv.drawRightString(w-1.8*cm,1.15*cm,str(doc.page))
    canv.restoreState()
for lang in ("RU","EN","DE","FR"):
    source=(ROOT/f"books/BOOK_{lang}.md").read_text(encoding="utf-8")
    lines=source.splitlines()
    name=lines[0].removeprefix("# ").strip()
    fname=OUT/f"VMESTE_Book_{lang}_2026.pdf"
    doc=SimpleDocTemplate(str(fname),pagesize=A4,
        leftMargin=1.8*cm,rightMargin=1.8*cm,topMargin=2*cm,bottomMargin=2.1*cm,
        title=name,author="VMESTE",subject="Open illustrated technology book series")
    story=[Spacer(1,1.4*cm),art("community"),Spacer(1,1.1*cm),
           Paragraph(inline(name),title),Spacer(1,.6*cm),
           Paragraph("RU · EN · DE · FR",sub),Spacer(1,1.5*cm),
           Paragraph('<link href="https://xn--b1aga0a0ag.site/" color="#12686D"><u>vmeste.site</u></link>',sub),
           PageBreak()]
    chapter=0
    buf=[]
    def flush():
        if not buf:return
        merged=" ".join(buf).strip()
        if merged:story.append(Paragraph(inline(merged),base))
        buf.clear()
    for line in lines[1:]:
        line=line.strip()
        if not line:
            flush()
        elif line.startswith("## "):
            flush()
            if chapter:story.append(Spacer(1, .65*cm))
            story.append(Paragraph(inline(line[3:]),heading))
            illustrations = {2:"community", 3:"ai", 4:"tashi", 5:"heat", 6:"tools", 7:"ai", 8:"robot", 9:"tools"}
            if chapter in illustrations:
                story.append(art(illustrations[chapter], 15.5*cm))
                story.append(Spacer(1,.35*cm))
            chapter+=1
        elif line.startswith("- "):
            flush()
            story.append(Paragraph("• "+inline(line[2:]),base))
        elif line.startswith("# "):
            flush()
            story.append(Paragraph(inline(line[2:]),heading))
        else:buf.append(line)
    flush()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(f"{fname}: {fname.stat().st_size} bytes")
