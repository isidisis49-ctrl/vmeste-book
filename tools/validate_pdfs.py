#!/usr/bin/env python3
"""Validate public PDFs: language, links, source text, geometry and page density."""
import argparse,hashlib,json,re,unicodedata
from pathlib import Path
import fitz
from build_pdfs import URLS,sections

def compact(s):return re.sub(r'\W+','',unicodedata.normalize('NFKC',s)).casefold()

def main():
 p=argparse.ArgumentParser();p.add_argument('--pdf-dir',type=Path);p.add_argument('--output',type=Path);p.add_argument('--compare-dir',type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[1];folder=a.pdf_dir or root/'downloads';cfg=json.loads((root/'books/editions.json').read_text());checks=[];reports=[]
 def check(name,value,detail=''):
  checks.append({'check':name,'status':'PASS' if value else 'FAIL','detail':detail})
 for lang in ['RU','EN','DE','FR']:
  path=folder/f'VMESTE_Book_{lang}_2026.pdf';d=fitz.open(path);text='\n'.join(page.get_text() for page in d);links={x.get('uri') for page in d for x in page.get_links() if x.get('uri')};raw_lang=d.xref_get_key(d.pdf_catalog(),'Lang')[1]
  check(lang+' / 10 substantial pages',len(d)==10)
  check(lang+' / document language',raw_lang==cfg[lang]['tag'],raw_lang)
  check(lang+' / six exact external targets',set(URLS)<=links)
  check(lang+' / no unsafe link targets',all(u.startswith('https://') for u in links))
  check(lang+' / no replacement characters','\ufffd' not in text)
  if lang!='RU':check(lang+' / no Cyrillic text or metadata',not re.search('[А-Яа-яЁё]',text+json.dumps(d.metadata,ensure_ascii=False)))
  _,_,story=sections(root/f'books/BOOK_{lang}.md');clean=compact(text)
  for i,chapter in enumerate(story[:10]):
   wanted=[chapter['heading']]+chapter['paras'];check(lang+f' / original section {i+1} retained',all(compact(s.strip('*')) in clean for s in wanted))
  if a.compare_dir:
   other=fitz.open(a.compare_dir/path.name);check(lang+' / rebuilt text equals published',compact(text)==compact(''.join(p.get_text() for p in other)))
  page_info=[]
  for i,page in enumerate(d):
   spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
   inside=all(s['bbox'][0]>=-0.5 and s['bbox'][1]>=-0.5 and s['bbox'][2]<=page.rect.width+.5 and s['bbox'][3]<=page.rect.height+.5 for s in spans)
   check(lang+f' / page {i+1} text inside sheet',inside)
   large=[s for s in spans if s['size']>=10.4];check(lang+f' / page {i+1} readable narrative',bool(large))
   images=page.get_image_info();count=len(page.get_text().strip());check(lang+f' / page {i+1} not nearly empty',(count>=400 or i==0) and bool(images))
   fonts={s['font'] for s in spans};check(lang+f' / page {i+1} expected fonts',all('DejaVu' in f for f in fonts),', '.join(sorted(fonts)))
   page_info.append({'page':i+1,'text_characters':count,'images':len(images),'minimum_text_pt':min(s['size'] for s in spans),'maximum_text_pt':max(s['size'] for s in spans)})
  reports.append({'language':lang,'pages':len(d),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'link_targets':sorted(links),'page_metrics':page_info})
 provenance=json.loads((root/'assets/screens/provenance.json').read_text())
 check('12 actual local screenshots',len(provenance['captures'])==12)
 check('No Cyrillic left in foreign screenshot DOM',all(not x['untranslated_cyrillic'] for x in provenance['captures'] if x['language']!='RU'))
 check('No production or personal data used',not provenance['production_contacted'] and not provenance['personal_data_used'])
 check('No screenshot pixel retouching',all(x['pixel_retouched'] is False for x in provenance['captures']))
 for item in provenance['captures']:
  check('Screenshot bytes / '+item['file'],hashlib.sha256((root/'assets/screens'/item['file']).read_bytes()).hexdigest()==item['sha256'])
 result={'summary':{'PASS':sum(c['status']=='PASS' for c in checks),'FAIL':sum(c['status']=='FAIL' for c in checks)},'checks':checks,'editions':reports,'limits':['Editorial UI localization is not a released multilingual product.','Remote link availability is distinct from exact embedded target validation.','Generated artwork was visually reviewed; OCR is advisory, not a proof of absence of all text.']}
 out=a.output or folder/'validation.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result['summary']))
 if result['summary']['FAIL']:
  for c in checks:
   if c['status']=='FAIL':print(c)
  raise SystemExit(1)
if __name__=='__main__':main()
