# -*- coding: utf-8 -*-
"""Fetch one batch of computerhope jargon articles via WebBridge same-origin fetch.
Usage: python wb_fetch_batch.py <start> <count>
Appends to dict_articles.jsonl: {"term":..., "url":..., "text":...}
"""
import sys, io, json, subprocess, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WS = r'C:\Users\Игорь\Documents\kimi\workspace'
start, count = int(sys.argv[1]), int(sys.argv[2])

links = json.load(open(os.path.join(WS, 'dict_links.json'), encoding='utf-8'))
items = list(links.items())
# dedupe by url, keep order
seen, uniq = set(), []
for t, u in items:
    if u not in seen:
        seen.add(u); uniq.append((t, u))
batch = uniq[start:start+count]
if not batch:
    print("EMPTY"); sys.exit(0)

js = """(async()=>{
const batch=%s;
const out=[];
for(const [term,url] of batch){
  try{
    const r=await fetch(url);
    const h=await r.text();
    const d=new DOMParser().parseFromString(h,'text/html');
    let main=d.querySelector('div.entry-content')||d.querySelector('#main')||d.querySelector('main')||d.body;
    let txt=(main.innerText||'').replace(/\\s+/g,' ').trim();
    out.push({term,url,status:r.status,text:txt.slice(0,2500)});
  }catch(e){out.push({term,url,status:0,text:'ERR '+e.message});}
  await new Promise(r=>setTimeout(r,300));
}
return JSON.stringify(out);})()""" % json.dumps(batch)

req = {"action": "evaluate", "args": {"code": js}, "session": "jnana-dict"}
reqfile = os.path.join(WS, 'wb-req-batch.json')
open(reqfile, 'w', encoding='utf-8').write(json.dumps(req))

r = subprocess.run(['curl.exe', '-s', '-X', 'POST', 'http://127.0.0.1:10086/command',
                    '-H', 'Content-Type: application/json',
                    '--data-binary', '@' + reqfile], capture_output=True)
resp = json.loads(r.stdout.decode('utf-8'))
val = resp['data']['value']
arts = json.loads(val)
with open(os.path.join(WS, 'dict_articles.jsonl'), 'a', encoding='utf-8') as f:
    for a in arts:
        f.write(json.dumps(a, ensure_ascii=False) + '\n')
print("fetched", len(arts), "ok:", sum(1 for a in arts if a['status'] == 200))
