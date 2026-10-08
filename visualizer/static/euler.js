/* Evidence-based Euler diagrams. Geometry never resolves an unknown relation. */
'use strict';
window.ConceptuumEuler = (() => {
  const colors = ['#207361','#527ba9','#a67934','#8c69ab','#b96758','#438c94','#7c8e45','#a8668d'];
  const esc = value => String(value ?? '').replace(/[&<>"']/g,c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const validID = value => Number.isSafeInteger(Number(value)) && Number(value)>0;
  const parseSelection = raw => [...new Set(String(raw || '').split(',').filter(validID).map(Number))].slice(0,8);
  const genusColors = ['#647b68','#718699','#927a62','#88718f'];
  const color = (id,ids) => ids.includes(Number(id)) ? colors[ids.indexOf(Number(id)) % colors.length] : genusColors[Number(id)%genusColors.length];
  const kindNames = {inside:'Contained in',contains:'Contains',equal:'Equal extension',overlap:'Overlap',disjoint:'Disjoint',unknown:'Unknown',conflict:'Conflicting records'};
  function lines(text, max=24) {
    const words=String(text).replace(/\s+/g,' ').split(' '), result=[];
    let line='';
    for (const word of words) {
      if (line && (line+' '+word).length>max) { result.push(line); line=''; }
      let rest=word;
      while (rest.length>max) { if (line) {result.push(line);line='';} result.push(rest.slice(0,max));rest=rest.slice(max); }
      line+=(line?' ':'')+rest;
    }
    if(line)result.push(line);
    return result.length>2 ? [result[0],result[1].slice(0,max-1)+'…'] : result;
  }
  function label(name,x,y,max=24,style='',scale=1) {
    const rows=lines(name,max), start=y-(rows.length-1)*8*scale;
    return `<text class="euler-label" text-anchor="middle" style="${style};font-size:${13*scale}px">${rows.map((row,i)=>`<tspan x="${x}" y="${start+i*16*scale}">${esc(row)}</tspan>`).join('')}</text>`;
  }
  function circle(concept,x,y,r,ids,{ghost=false,dash='',offset=0,automatic=false}={}) {
    const ink=color(concept.id,ids);
    return `<g class="euler-region${ghost?' unknown':''}${automatic?' automatic':''}" data-euler-inspect="${concept.id}" role="button" tabindex="0" aria-label="Inspect ${esc(concept.nama)}${automatic?' (automatic shared genus)':''}"><title>${esc(concept.nama)}${automatic?' — shared genus, added automatically':''}</title><circle class="euler-circle" cx="${x}" cy="${y}" r="${r}" fill="${ink}" stroke="${ink}"${dash?` stroke-dasharray="${dash}" stroke-dashoffset="${offset}"`:''}/></g>`;
  }
  function relationDescription(pair,byID) {
    const a=byID.get(pair.a)?.nama || `#${pair.a}`,b=byID.get(pair.b)?.nama || `#${pair.b}`;
    return ({inside:`${a} is included in ${b}`,contains:`${a} contains ${b}`,equal:`${a} and ${b} have equal extension`,overlap:`${a} and ${b} overlap`,disjoint:`${a} and ${b} are disjoint`,unknown:`The relationship between ${a} and ${b} is unknown`,conflict:`The records for ${a} and ${b} cannot be drawn consistently`})[pair.kind];
  }
  function pairDrawing(pair,byID,ids) {
    const a=byID.get(pair.a),b=byID.get(pair.b),nodes=[];
    let html='';
    function add(c,x,y,r,opts={}) { html+=circle(c,x,y,r,ids,opts);nodes.push({id:c.id,x,y}); }
    if(pair.kind==='inside'||pair.kind==='contains') {
      const parent=pair.kind==='inside'?b:a,child=pair.kind==='inside'?a:b;
      add(parent,170,143,87);add(child,170,165,50);
      html+=label(parent.nama,170,91,25)+label(child.nama,170,168,15);
    } else if(pair.kind==='equal') {
      add(a,170,143,85,{dash:'9 9'});add(b,170,143,85,{dash:'9 9',offset:9});
      html+=label(a.nama,170,111,24)+'<text class="euler-symbol" x="170" y="149" text-anchor="middle">=</text>'+label(b.nama,170,179,24);
    } else if(pair.kind==='overlap') {
      add(a,134,145,76);add(b,206,145,76);
      html+=label(a.nama,108,145,14)+label(b.nama,232,145,14);
    } else if(pair.kind==='disjoint') {
      add(a,91,145,65);add(b,249,145,65);
      html+=label(a.nama,91,145,17)+label(b.nama,249,145,17);
    } else {
      add(a,92,145,57,{ghost:true});add(b,248,145,57,{ghost:true});
      html+=label(a.nama,92,145,15)+label(b.nama,248,145,15);
      html+=`<text class="euler-symbol" x="170" y="150" text-anchor="middle">${pair.kind==='conflict'?'!':'?'}</text>`;
    }
    return {html,nodes};
  }

  function groupsFor(data) {
    const parent=new Map(data.concepts.map(c=>[c.id,c.id]));
    function root(id) { while(parent.get(id)!==id)id=parent.get(id);return id; }
    for(const p of data.pairs)if(p.kind==='equal')parent.set(root(p.b),root(p.a));
    const groups=new Map();
    for(const c of data.concepts) {
      const key=root(c.id);
      if(!groups.has(key))groups.set(key,{id:key,concepts:[],children:[],parent:null});
      groups.get(key).concepts.push(c);
    }
    const kinds=new Map();
    for(const p of data.pairs) {
      kinds.set(`${p.a}:${p.b}`,p.kind);
      kinds.set(`${p.b}:${p.a}`,({inside:'contains',contains:'inside'})[p.kind]||p.kind);
    }
    return {items:[...groups.values()],kinds};
  }
  // A fast, stable layout for a hierarchy. Unknown siblings may share a genus,
  // but their dashed outlines explicitly leave their mutual relation open.
  function forestModel(data) {
    if(data.pairs.some(p=>['conflict','overlap'].includes(p.kind)))return null;
    const {items,kinds}=groupsFor(data);
    for(const g of items) {
      const candidates=items.filter(other=>other!==g&&kinds.get(`${g.id}:${other.id}`)==='inside');
      if(candidates.length) {
        const closest=candidates.find(p=>candidates.every(other=>other===p||kinds.get(`${p.id}:${other.id}`)==='inside'));
        if(!closest)return null;
        g.parent=closest;closest.children.push(g);
      }
    }
    // Unrelated roots still need evidence; unknown siblings have a known genus.
    for(const g of [{children:items.filter(g=>!g.parent)},...items]) {
      for(let i=0;i<g.children.length;i++)for(const other of g.children.slice(i+1)) {
        const kind=kinds.get(`${g.children[i].id}:${other.id}`);
        if(kind!=='disjoint'&&!(g.id&&kind==='unknown'))return null;
      }
    }
    function size(g,path=new Set()) {
      if(path.has(g.id))throw new Error('Cyclic circle nesting');
      const next=new Set([...path,g.id]);g.children.forEach(child=>size(child,next));
      if(!g.children.length)g.r=Math.max(86,38+g.concepts.length*24);
      else if(g.children.length===1) {
        g.children[0].dx=0;g.children[0].dy=23;
        g.r=g.children[0].r+54+Math.max(0,g.concepts.length-1)*46;
      } else {
        const cols=Math.ceil(Math.sqrt(g.children.length)),rows=Math.ceil(g.children.length/cols),step=2*Math.max(...g.children.map(c=>c.r))+22;
        g.r=0;
        g.children.forEach((child,index)=>{
          const row=Math.floor(index/cols),columns=Math.min(cols,g.children.length-row*cols);
          child.dx=(index%cols-(columns-1)/2)*step;child.dy=(row-(rows-1)/2)*step+35;
          g.r=Math.max(g.r,Math.hypot(child.dx,child.dy)+child.r+36);
        });
        g.r+=Math.max(0,g.concepts.length-1)*46;
      }
    }
    const roots=items.filter(g=>!g.parent);
    if(!roots.length&&items.length)return null;
    try{roots.forEach(g=>size(g));}catch(_){return null;}
    return roots;
  }

  // A layout is published only after ALL known pair constraints are checked.
  // This also catches cross-branch constraints and inconsistent equal aliases.
  function validGeometry(data,items) {
    const byID=new Map();
    for(const g of items)for(const c of g.concepts)byID.set(c.id,g);
    if(items.some(g=>![g.x,g.y,g.r].every(Number.isFinite)||g.r<=0))return false;
    return data.pairs.every(p=>{
      const a=byID.get(p.a),b=byID.get(p.b);
      if(!a||!b)return false;
      const d=Math.hypot(a.x-b.x,a.y-b.y);
      return ({inside:()=>d+a.r<b.r-2,contains:()=>d+b.r<a.r-2,
        equal:()=>d<.01&&Math.abs(a.r-b.r)<.01,
        overlap:()=>d>Math.abs(a.r-b.r)+2&&d<a.r+b.r-2,
        disjoint:()=>d>a.r+b.r+2,unknown:()=>true,conflict:()=>false})[p.kind]?.()||false;
    });
  }

  // Bounded deterministic circle-constraint projection. Radius is allowed to
  // change, so a species can fit inside the intersection of multiple genera.
  // No areas or higher-order intersections are inferred from this geometry.
  function overlapModel(data,compact) {
    if(data.pairs.some(p=>p.kind==='conflict'))return null;
    const {items,kinds}=groupsFor(data),count=items.length;
    const constraints=[];
    for(let i=0;i<count;i++)for(let j=i+1;j<count;j++) {
      constraints.push({i,j,kind:kinds.get(`${items[i].id}:${items[j].id}`)||'unknown'});
    }
    // Don't imply a relationship between disconnected, unrecorded selections.
    if(constraints.some(p=>p.kind==='unknown')) {
      const seen=new Set([0]);
      for(let n=0;n<count;n++)for(const p of constraints) {
        if(['inside','contains','overlap'].includes(p.kind)&&(seen.has(p.i)||seen.has(p.j))) {seen.add(p.i);seen.add(p.j);}
      }
      if(seen.size!==count)return null;
    }
    function depth(index,path=new Set()) {
      if(path.has(index))return count;
      const children=items.map((g,i)=>i).filter(i=>kinds.get(`${items[i].id}:${items[index].id}`)==='inside');
      return children.length?1+Math.max(...children.map(i=>depth(i,new Set([...path,index])))):0;
    }
    const ranks=items.map((g,i)=>depth(i));
    if(ranks.some(rank=>rank>=count))return null;
    const minimum=items.map(g=>Math.max(1,.45+g.concepts.length*.38));
    for(let attempt=0;attempt<6;attempt++) {
      const nodes=items.map((g,i)=>{
        const angle=2*Math.PI*i/count+attempt*.71,spread=1.4+count*.1;
        return {x:Math.cos(angle)*spread,y:Math.sin(angle)*spread,r:minimum[i]+ranks[i]*.9};
      });
      // Put each initial genus near its descendants, retaining distinct leaves.
      items.map((_,i)=>i).sort((a,b)=>ranks[a]-ranks[b]).forEach(i=>{
        const children=nodes.filter((_,j)=>kinds.get(`${items[j].id}:${items[i].id}`)==='inside');
        if(children.length) {nodes[i].x=children.reduce((s,c)=>s+c.x,0)/children.length;nodes[i].y=children.reduce((s,c)=>s+c.y,0)/children.length-.3;}
      });
      function project(a,b,violation,gd,ga,gb) {
        if(violation<=0)return;
        const d=Math.hypot(a.x-b.x,a.y-b.y),ux=d>1e-8?(a.x-b.x)/d:Math.cos(attempt+.7),uy=d>1e-8?(a.y-b.y)/d:Math.sin(attempt+.7);
        const step=violation*.82/(2*gd*gd+.3*(ga*ga+gb*gb));
        a.x-=step*gd*ux;a.y-=step*gd*uy;b.x+=step*gd*ux;b.y+=step*gd*uy;
        a.r-=step*.3*ga;b.r-=step*.3*gb;
      }
      for(let iteration=0;iteration<1200;iteration++) {
        for(const p of constraints) {
          let a=nodes[p.i],b=nodes[p.j],kind=p.kind;
          if(kind==='contains') {[a,b]=[b,a];kind='inside';}
          const d=Math.hypot(a.x-b.x,a.y-b.y);
          if(kind==='inside')project(a,b,d+a.r-b.r+.36,1,1,-1);
          else if(kind==='disjoint')project(a,b,a.r+b.r+.3-d,-1,1,1);
          else if(kind==='overlap') {
            project(a,b,d-a.r-b.r+.45,1,-1,-1);
            project(a,b,Math.abs(a.r-b.r)+.45-Math.hypot(a.x-b.x,a.y-b.y),-1,a.r>=b.r?1:-1,a.r>=b.r?-1:1);
          }
          // A soft spacing preference keeps labels and unconstrained siblings
          // apart; it is disabled during the final constraint-only refinement.
          if(iteration<950&&d>1e-6&&['overlap','unknown'].includes(kind)) {
            const target=kind==='overlap'?Math.abs(a.r-b.r)+Math.min(a.r,b.r)*1.15:a.r+b.r+.3;
            const shift=(d-target)*.004,ux=(a.x-b.x)/d,uy=(a.y-b.y)/d;
            a.x-=shift*ux;a.y-=shift*uy;b.x+=shift*ux;b.y+=shift*uy;
          }
        }
        nodes.forEach((g,i)=>{g.r=Math.max(minimum[i],Math.min(count*3,g.r));});
        if(iteration%100===99) {
          const candidate=items.map((g,i)=>({...g,x:nodes[i].x*80,y:nodes[i].y*80,r:nodes[i].r*80}));
          if(iteration>=999&&validGeometry(data,candidate)) {
            const width=Math.max(...candidate.map(g=>g.x+g.r))-Math.min(...candidate.map(g=>g.x-g.r));
            const height=Math.max(...candidate.map(g=>g.y+g.r))-Math.min(...candidate.map(g=>g.y-g.r));
            if(compact&&width>height*1.2)candidate.forEach(g=>{[g.x,g.y]=[g.y,g.x];});
            return candidate;
          }
        }
      }
    }
    return null;
  }

  const layoutCache=new WeakMap();
  function combinedModel(data,compact) {
    let cached=layoutCache.get(data);
    if(!cached) {cached={};layoutCache.set(data,cached);}
    const key=compact?'compact':'wide';
    if(key in cached)return cached[key];
    const roots=forestModel(data),items=[];
    if(roots) {
      const radius=Math.max(...roots.map(g=>g.r)),cols=compact?1:Math.ceil(Math.sqrt(roots.length)),step=radius*2+65;
      function place(g,x,y) {g.x=x;g.y=y;items.push(g);g.children.forEach(c=>place(c,x+c.dx,y+c.dy));}
      roots.forEach((g,i)=>place(g,(i%cols)*step,Math.floor(i/cols)*step));
      if(validGeometry(data,items))return cached[key]=items;
    }
    return cached[key]=overlapModel(data,compact);
  }

  function drawCombined(data,items,ids,result,fontScale) {
    const automatic=new Set((data.automatic||[]).map(g=>g.id));
    const uncertain=new Set(data.pairs.filter(p=>p.kind==='unknown').flatMap(p=>[p.a,p.b]));
    const ordered=[...items].sort((a,b)=>b.r-a.r),boxes=[];
    for(const g of ordered)g.concepts.forEach((c,i)=>{
      const opts={ghost:uncertain.has(c.id),automatic:automatic.has(c.id)};
      if(g.concepts.length>1)Object.assign(opts,{dash:`8 ${8*(g.concepts.length-1)}`,offset:8*i});
      result.html+=circle(c,g.x,g.y,g.r,ids,opts);
      result.nodes.push({id:c.id,x:g.x,y:g.y,r:g.r});
    });
    // Choose label positions inside their own circle and outside other regions
    // where possible. All labels are drawn above all translucent circle fills.
    for(const g of ordered) {
      const nested=items.some(other=>other!==g&&Math.hypot(other.x-g.x,other.y-g.y)+other.r<g.r);
      const max=Math.max(6,Math.min(30,Math.floor(g.r/(4*fontScale)))),width=data.catalog?28*fontScale:Math.min(g.r*1.6,max*7*fontScale+8);
      const height=(g.concepts.length*(data.catalog?32:44)+(!data.catalog&&g.concepts.some(c=>automatic.has(c.id))?14:0))*fontScale;
      const candidates=[{x:g.x,y:nested?g.y-g.r+32*fontScale:g.y}];
      for(const fraction of [.45,.65,.25,0])for(let k=0;k<16;k++) {
        const angle=-Math.PI/2+k*Math.PI/8;
        candidates.push({x:g.x+Math.cos(angle)*g.r*fraction,y:g.y+Math.sin(angle)*g.r*fraction});
      }
      let best=null;
      for(const [index,c] of candidates.entries()) {
        const box={x:c.x-width/2,y:c.y-height/2,w:width,h:height};
        let score=index*.1;
        for(const dx of [-width/2,width/2])for(const dy of [-height/2,height/2])score+=Math.max(0,Math.hypot(c.x+dx-g.x,c.y+dy-g.y)-g.r+6)*100;
        for(const b of boxes)if(box.x<b.x+b.w&&box.x+box.w>b.x&&box.y<b.y+b.h&&box.y+box.h>b.y)score+=3000;
        for(const other of items)if(other!==g&&Math.hypot(g.x-other.x,g.y-other.y)+g.r>other.r+1) {
          const nearX=Math.max(box.x,Math.min(other.x,box.x+box.w)),nearY=Math.max(box.y,Math.min(other.y,box.y+box.h));
          score+=Math.max(0,other.r-Math.hypot(nearX-other.x,nearY-other.y))*3;
        }
        if(!best||score<best.score)best={...c,box,score};
      }
      boxes.push(best.box);
      result.labelBoxes.push(best.box);
      g.concepts.forEach((c,i)=>{
        const y=best.y+(i-(g.concepts.length-1)/2)*44*fontScale;
        const name=data.catalog?String.fromCharCode(65+data.concepts.indexOf(c)):c.nama;
        result.html+=label(name,best.x,y,max,`fill:${color(c.id,ids)}`,fontScale);
        if(automatic.has(c.id)&&!data.catalog)result.html+=`<text class="euler-auto-label" text-anchor="middle" style="font-size:${10*fontScale}px" x="${best.x}" y="${y+23*fontScale}">shared genus · auto</text>`;
      });
    }
  }

  function render(data,{ids,compact=false,page=0,mode='auto',width=900,height=620}={}) {
    ids=ids||data.concepts.map(c=>c.id);
    const byID=new Map(data.concepts.map(c=>[c.id,c]));
    const result={html:'',nodes:[],labelBoxes:[],bounds:null,totalPages:1,page:0,summary:'',notice:'',layout:'combined'};
    if(!data.concepts.length)return result;
    const items=mode==='auto'||data.concepts.length===1?combinedModel(data,compact):null;
    if(items) {
      const nodes=items;
      result.bounds={minX:Math.min(...nodes.map(n=>n.x-n.r))-24,maxX:Math.max(...nodes.map(n=>n.x+n.r))+24,minY:Math.min(...nodes.map(n=>n.y-n.r))-24,maxY:Math.max(...nodes.map(n=>n.y+n.r))+48};
      const b=result.bounds,scale=Math.max(.12,Math.min(1.1,(width-40)/(b.maxX-b.minX),(height-130)/(b.maxY-b.minY+12)));
      drawCombined(data,items,ids,result,Math.min(2.8,Math.max(1,11/(13*scale))));
      result.notice='Nested circles show inclusion; crossing circles show recorded partial overlap. Areas are illustrative.';
      if(data.pairs.some(p=>p.kind==='unknown'))result.notice+=' Dashed circles have unspecified relationships; spacing is not evidence.';
      if(data.pairs.some(p=>p.kind==='overlap')&&data.concepts.length>2)result.notice+=' Multi-set regions illustrate one possible layout.';
      const auto=(data.automatic||[]).length;
      result.summary=`${data.concepts.length-auto} selected${auto?` + ${auto} shared ${auto===1?'genus':'genera'}`:''} · Euler diagram`;
    } else {
      result.layout='pairs';
      const size=compact?1:4,totalPages=Math.max(1,Math.ceil(data.pairs.length/size));
      page=Math.min(page,totalPages-1);result.page=page;result.totalPages=totalPages;
      const current=data.pairs.slice(page*size,(page+1)*size),cols=compact?1:Math.min(2,current.length);
      current.forEach((pair,index)=>{
        const x=(index%cols)*360,y=Math.floor(index/cols)*295;
        const drawing=pairDrawing(pair,byID,ids);
        const description=relationDescription(pair,byID);
        const foot=pair.kind==='unknown'?'Unknown does not mean disjoint.':pair.kind==='conflict'?'No consistent circles asserted.':'Circle areas are illustrative.';
        result.html+=`<g class="euler-pair" data-kind="${pair.kind}" transform="translate(${x},${y})"><title>${esc(description)}</title><rect class="euler-pair-frame" width="340" height="277" rx="12"/><text class="euler-pair-title" x="17" y="27">${esc(kindNames[pair.kind])}</text><text class="euler-provenance" text-anchor="end" x="324" y="27">${pair.kind==='unknown'?'No record':pair.kind==='conflict'?'Review needed':pair.inferred?'Via hierarchy / equality':'Recorded'}</text>${drawing.html}<text class="euler-pair-foot" text-anchor="middle" x="170" y="260">${foot}</text></g>`;
        drawing.nodes.forEach(n=>result.nodes.push({...n,x:n.x+x,y:n.y+y}));
      });
      result.bounds={minX:-10,minY:-10,maxX:cols*360-10,maxY:Math.ceil(current.length/cols)*295-8};
      result.summary=`${page*size+1}–${page*size+current.length} of ${data.pairs.length} pairs`;
      if(data.pairs.some(p=>p.kind==='conflict'))result.notice='Some records cannot be drawn consistently. They are marked for review instead of forcing a circle layout.';
      else if(data.pairs.some(p=>p.kind==='unknown'))result.notice='Unrecorded relationships use dashed placeholders. Unknown does not mean disjoint.';
      else result.notice='Each pair is shown separately. Pairwise overlap does not determine a shared intersection of three or more concepts.';
      if(mode==='auto'&&!data.pairs.some(p=>p.kind==='conflict'||p.kind==='unknown'))result.notice='A combined circle layout could not satisfy every recorded relationship. Compare the pairs below.';
    }
    if(result.bounds) {
      const b=result.bounds;
      const unknown=data.pairs.some(p=>p.kind==='unknown'),overlap=data.pairs.some(p=>p.kind==='overlap');
      const note=result.layout==='pairs'?'Independent pair comparisons':unknown?'Dashed: some relationships unknown':overlap&&data.concepts.length>2?'Multi-set regions are illustrative':'Recorded set relationships';
      result.html+=`<text class="euler-scale-note" text-anchor="middle"><tspan x="${(b.minX+b.maxX)/2}" y="${b.maxY-8}">Areas are illustrative</tspan><tspan x="${(b.minX+b.maxX)/2}" y="${b.maxY+5}">${note}</tspan></text>`;
      b.maxY+=12;
    }
    if(data.omitted_genera)result.notice+=` ${data.omitted_genera} additional shared genera are omitted; narrow the selection to show them.`;
    return result;
  }
  return {parseSelection,color,render,relationDescription,maxConcepts:8};
})();
