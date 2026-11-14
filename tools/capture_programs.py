#!/usr/bin/env python3
"""Capture real LOCAL review programs. Editorial UI localization, never pixel retouching.
No production requests, accounts, messages, actual Ollama calls or personal data.
"""
import argparse,hashlib,json,sys,tempfile,threading,re,mimetypes
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
from unittest.mock import patch

LOCALIZE = r'''({selector,dictionary,lang}) => {
 const root=document.querySelector(selector);const rx=/[А-Яа-яЁё]/;
 function translated(text){
  const key=text.replace(/\s+/g,' ').trim();
  if(dictionary[key])return text.replace(key,dictionary[key]);
  let m=key.match(/^(\d+) эт\.$/);if(m)return lang==='EN'?'Level '+m[1]:lang==='DE'?'Ebene '+m[1]:'Niveau '+m[1];
  m=key.match(/^Вход (\d+)$/);if(m)return (lang==='EN'?'Entrance ':lang==='DE'?'Eingang ':'Entrée ')+m[1];
  m=key.match(/^Подъезд (\d+)$/);if(m)return (lang==='EN'?'Stairwell ':lang==='DE'?'Treppenhaus ':'Cage ')+m[1];
  return text;
 }
 function apply(){
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;let nodes=[];
  while(n=walker.nextNode()){if(!['SCRIPT','STYLE'].includes(n.parentElement.tagName))nodes.push(n);}
  for(const n of nodes){const value=translated(n.textContent);if(value!==n.textContent)n.textContent=value;}
  for(const n of root.querySelectorAll('[placeholder],input')){
   const p=n.getAttribute('placeholder');if(p){const v=translated(p);if(v!==p)n.setAttribute('placeholder',v);}
   if(n.tagName==='INPUT'&&rx.test(n.value)){const v=translated(n.value);if(v!==n.value)n.value=v;}
  }
 }
 apply();const observer=new MutationObserver(apply);observer.observe(root,{subtree:true,childList:true,characterData:true});
 window.__bookTranslationObserver=observer;
}'''

CHECK = r'''selector => {
 const root=document.querySelector(selector),rx=/[А-Яа-яЁё]/,out=[];
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;
 while(n=walker.nextNode()){
  const e=n.parentElement;if(['SCRIPT','STYLE'].includes(e.tagName))continue;
  const box=e.getBoundingClientRect();if(box.width&&box.height&&getComputedStyle(e).visibility!=='hidden'&&rx.test(n.textContent))out.push(n.textContent.trim());
 }
 for(const e of root.querySelectorAll('input'))if(e.getBoundingClientRect().width&&rx.test(e.value||e.placeholder))out.push(e.value||e.placeholder);
 return [...new Set(out)];
}'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--vesta-source',required=True,type=Path);p.add_argument('--site-dist',required=True,type=Path);p.add_argument('--site-public',required=True,type=Path);p.add_argument('--heating-html',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--chromium',default='/usr/bin/chromium');a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(a.vesta_source.resolve()));import app,settings,drafts
 from playwright.sync_api import sync_playwright
 locale_file=Path(__file__).resolve().parents[1]/'assets/ui-locales.json';locales=json.loads(locale_file.read_text())
 servers=[];records=[];assets_used={}
 class Site(SimpleHTTPRequestHandler):
  def do_GET(self):
   path=self.path.split('?')[0]
   if path.startswith('/api/'):
    b=b'{"detail":"Anonymous local review"}';self.send_response(401);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
   if path=='/heating-view.html':file=a.heating_html
   elif path.startswith('/illustrations/approved-cartoon/'):
    file=(a.site_public/path.lstrip('/')).resolve()
    if not file.is_relative_to(a.site_public.resolve()):self.send_error(403);return
   else:file=None
   if file:
    if not file.is_file():self.send_error(404);return
    b=file.read_bytes();assets_used[path]=hashlib.sha256(b).hexdigest();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(file.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
   if not Path(self.translate_path(path)).exists():self.path='/index.html'
   return super().do_GET()
  def log_message(self,*_):pass
 def start(handler):
  s=ThreadingHTTPServer(('127.0.0.1',0),handler);t=threading.Thread(target=s.serve_forever,daemon=True);t.start();servers.append((s,t));return f'http://127.0.0.1:{s.server_port}'
 with tempfile.TemporaryDirectory(prefix='vmeste-book-capture-') as tmp:
  app.DATA=Path(tmp);app.DB=Path(tmp)/'history.sqlite3';settings.SETTINGS_FILE=Path(tmp)/'settings.json';drafts.DRAFT_DB=Path(tmp)/'drafts.sqlite3'
  with patch.object(app,'check_ollama',return_value=False),patch.object(app,'voice_available',return_value=False):
   va=start(app.Handler);site=start(partial(Site,directory=str(a.site_dist)))
   try:
    with sync_playwright() as pw:
     b=pw.chromium.launch(executable_path=a.chromium,headless=True,args=['--no-sandbox']);c=b.new_context(viewport={'width':1200,'height':1000},device_scale_factor=1.5)
     blocked=[]
     def route(r):
      if r.request.url.startswith((va+'/',site+'/')):r.continue_()
      else:blocked.append(r.request.url.split('?')[0]);r.abort()
     c.route('**/*',route)
     page=c.new_page()
     for lang in ['RU','EN','DE','FR']:
      for name,url,selector in [('vesta',va,'#matching-panel'),('heating',site+'/heating-view.html','#building-panel'),('tools',site+'/my-tools','.vm-my-tools')]:
       page.goto(url);page.wait_for_selector(selector,state='visible');page.wait_for_timeout(500)
       if name=='tools':
        page.locator('img').evaluate_all("xs=>xs.forEach(x=>x.loading='eager')");page.wait_for_timeout(500)
        broken=page.locator(selector+' img').evaluate_all('xs=>xs.filter(x=>!x.complete||!x.naturalWidth).map(x=>x.src)')
        if broken:raise RuntimeError('Broken source assets: '+str(broken))
       if lang!='RU':page.evaluate(LOCALIZE,{'selector':selector,'dictionary':locales[lang],'lang':lang});page.wait_for_timeout(150)
       remaining=page.evaluate(CHECK,selector) if lang!='RU' else []
       if remaining:raise RuntimeError('Untranslated '+lang+'/'+name+': '+str(remaining))
       out=a.output/f'{name}-{lang}.png'
       if name=='vesta':
        # A bounded real form fragment, not a redrawn interface or a generated mockup.
        page.locator(selector).scroll_into_view_if_needed();box=page.locator(selector).bounding_box();box['height']=min(690,box['height']);page.screenshot(path=str(out),clip=box)
       else:page.locator(selector).screenshot(path=str(out))
       records.append({'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'language':lang,'program':name,'local_review_build':True,'editorial_ui_translation':lang!='RU','pixel_retouched':False,'untranslated_cyrillic':remaining})
       print('CAPTURE_OK',lang,name,flush=True)
     b.close()
   finally:
    for s,t in servers:s.shutdown();s.server_close();t.join(3)
 manifest={'captures':records,'vesta_source_sha256':{n:hashlib.sha256((a.vesta_source/n).read_bytes()).hexdigest() for n in ['app.py','index.html','request_catalog_flow.js']},'heating_source_sha256':hashlib.sha256(a.heating_html.read_bytes()).hexdigest(),'local_assets_sha256':assets_used,'production_contacted':False,'personal_data_used':False,'actual_ollama_or_microphone':False,'note':'Actual local programs; foreign UI labels editorially translated, not a shipped multilingual release. Simulation readings are not physical measurements.'}
 (a.output/'provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
