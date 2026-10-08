/* Finite catalog sets: exact membership, Boolean operations, and real-data demos. */
'use strict';
window.ConceptuumEulerCatalog = (() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const operations=['none','intersection','union','difference','xor','complement','all','region'];
  const demos=[
    {id:'judgment-grid',title:'Cross-cutting classifications',context:5,ids:[2505,2506,2508,2509],basis:'catalog',op:'intersection',a:2505,b:2509,
      description:'Judgments are classified by quality and quantity. Universal affirmative judgments belong to both the affirmative and universal sets.'},
    {id:'shared-intersection',title:'Three-way intersection',context:5,ids:[2415,2420,2424],basis:'catalog',op:'all',a:2415,b:2420,
      description:'Judgment concepts belong to both thought content and logical form. Highlight all three sets together and inspect their shared members.'},
    {id:'judgment-union',title:'Union and difference',context:5,ids:[2505,2509],basis:'catalog',op:'union',a:2505,b:2509,
      description:'Combine affirmative and universal judgment concepts. Switch to A minus B or symmetric difference to see which records remain.'},
    {id:'judgment-complement',title:'Complement within a universe',context:5,ids:[2505,2506],basis:'catalog',op:'complement',a:2505,b:2506,
      description:'The automatic judgment genus defines the displayed universe. Its catalog contains other forms too: outside A is broader than the negative-judgment set.'},
    {id:'empty-intersection',title:'An empty intersection',context:5,ids:[2505,2506,2509],basis:'catalog',op:'intersection',a:2505,b:2506,
      description:'No stored concept belongs to both affirmative and negative judgment sets. Universal judgments cross each of them separately.'},
    {id:'language-equality',title:'Equality within a hierarchy',context:3,ids:[370,401,369,354],basis:'relations',op:'none',
      description:'Machine language and first-generation language have equal extension. Their coincident circles lie inside low-level and programming language.'},
    {id:'inherited-exclusion',title:'Inherited exclusion',context:1,ids:[104,4519,4783],basis:'relations',op:'none',
      description:'Mammals are inside vertebrates. The recorded vertebrate–invertebrate exclusion also separates mammals from invertebrates.'}
  ];
  function evaluate(data,{op='none',a,b,region=0,ids=[]}={}) {
    const concepts=data.concepts||[],catalog=data.catalog;
    if(!catalog)return {count:0,regions:[],samples:[],formula:''};
    const bit=id=>{const i=concepts.findIndex(c=>c.id===Number(id));return i<0?0:1<<i;};
    const ab=bit(a),bb=bit(b),all=ids.reduce((mask,id)=>mask|bit(id),0);
    const letter=id=>{const i=concepts.findIndex(c=>c.id===Number(id));return i<0?'?':String.fromCharCode(65+i);};
    const A=letter(a),B=letter(b);
    const formula=({none:'U',intersection:`${A} ∩ ${B}`,union:`${A} ∪ ${B}`,difference:`${A} ∖ ${B}`,xor:`${A} △ ${B}`,complement:`U ∖ ${A}`,all:ids.map(letter).join(' ∩ '),region:`Region ${regionName(data,region)}`})[op]||'U';
    const regions=catalog.regions.filter(r=>{
      const inA=Boolean(r.mask&ab),inB=Boolean(r.mask&bb);
      return ({intersection:()=>inA&&inB,union:()=>inA||inB,difference:()=>inA&&!inB,xor:()=>inA!==inB,
        complement:()=>!inA,all:()=>all>0&&(r.mask&all)===all,region:()=>r.mask===Number(region),none:()=>true})[op]?.()??true;
    });
    return {count:regions.reduce((sum,r)=>sum+r.count,0),regions,samples:regions.flatMap(r=>r.samples).slice(0,12),formula};
  }
  function regionName(data,mask) {
    return data.concepts.filter((c,i)=>mask&(1<<i)).map(c=>String.fromCharCode(65+data.concepts.indexOf(c))).join(' ∩ ')||'Outside all sets';
  }
  function regionDescription(data,mask) {
    return data.concepts.map((c,i)=>`${mask&(1<<i)?'in':'outside'} ${c.nama}`).join('; ');
  }
  function regionPoints(data,model) {
    const circles=data.concepts.map(c=>model.nodes.find(n=>n.id===c.id)),points=new Map(),b=model.bounds;
    if(circles.some(c=>!c||!Number.isFinite(c.r)))return points;
    const required=new Set(data.catalog.regions.map(r=>r.mask));
    function consider(x,y) {
      let mask=0,clearance=Infinity;
      circles.forEach((c,i)=>{const d=Math.hypot(x-c.x,y-c.y);if(d<c.r)mask|=1<<i;clearance=Math.min(clearance,Math.abs(d-c.r));});
      if(!required.has(mask)||clearance<.2)return;
      let score=clearance;
      for(const box of model.labelBoxes||[]) {
        const dx=Math.max(box.x-x,0,x-box.x-box.w),dy=Math.max(box.y-y,0,y-box.y-box.h);
        score=Math.min(score,Math.hypot(dx,dy));
      }
      if(!points.has(mask)||points.get(mask).score<score)points.set(mask,{x,y,score,clearance});
    }
    for(let ix=0;ix<=90;ix++)for(let iy=0;iy<=90;iy++)consider(b.minX+(b.maxX-b.minX)*ix/90,b.minY+(b.maxY-b.minY)*iy/90);
    for(const c of circles) {
      consider(c.x,c.y);
      for(const fraction of [.2,.45,.7,.88,.97])for(let i=0;i<48;i++)consider(c.x+c.r*fraction*Math.cos(i*Math.PI/24),c.y+c.r*fraction*Math.sin(i*Math.PI/24));
    }
    return points;
  }
  function decorate(data,model,options) {
    if(!data.catalog)return model;
    const catalog=data.catalog,selected=evaluate(data,options);
    model.notice='Catalog sets include roots and recorded descendants. U = all displayed sets. Counts describe stored concepts, not real-world instances.';
    model.summary=`${catalog.universe_count} stored concepts · ${catalog.regions.length} occupied regions`;
    if(model.layout!=='combined') {
      model.notice+=' Use Regions & members for exact results beyond pair comparisons.';return model;
    }
    const points=regionPoints(data,model);
    if(catalog.regions.some(r=>!points.has(r.mask))) {
      const pairs=window.ConceptuumEuler.render(data,{...options,mode:'pairs'});
      pairs.notice=model.notice+' Some occupied regions do not fit this circle layout. Exact memberships remain available in Regions & members.';
      pairs.summary=model.summary;return pairs;
    }
    const b=model.bounds,box=`x="${b.minX}" y="${b.minY}" width="${b.maxX-b.minX}" height="${b.maxY-b.minY}"`;
    const circles=data.concepts.map(c=>model.nodes.find(n=>n.id===c.id));
    const shape=(c,fill)=>`<circle cx="${c.x}" cy="${c.y}" r="${c.r}" fill="${fill}"/>`;
    let defs='<defs><pattern id="catalog-hatch" patternUnits="userSpaceOnUse" width="9" height="9"><path d="M0 9L9 0" stroke="#9b9681" stroke-width="1"/></pattern>';
    circles.forEach((c,i)=>{defs+=`<clipPath id="catalog-circle-${i}">${shape(c,'white')}</clipPath>`;});
    defs+=`<mask id="catalog-union" maskUnits="userSpaceOnUse" ${box}>${circles.map(c=>shape(c,'white')).join('')}</mask>`;
    for(const r of catalog.regions) {
      let intersection=`<rect ${box} fill="white"/>`;
      circles.forEach((c,i)=>{if(r.mask&(1<<i))intersection=`<g clip-path="url(#catalog-circle-${i})">${intersection}</g>`;});
      defs+=`<mask id="catalog-region-${r.mask}" maskUnits="userSpaceOnUse" ${box}>${intersection}${circles.filter((c,i)=>!(r.mask&(1<<i))).map(c=>shape(c,'black')).join('')}</mask>`;
    }
    defs+=`<mask id="catalog-empty" maskUnits="userSpaceOnUse" ${box}><rect ${box} fill="white" mask="url(#catalog-union)"/>${catalog.regions.map(r=>`<rect ${box} fill="black" mask="url(#catalog-region-${r.mask})"/>`).join('')}</mask></defs>`;
    let overlay=`<g class="catalog-regions" pointer-events="none"><rect ${box} fill="url(#catalog-hatch)" opacity=".45" mask="url(#catalog-empty)"/>`;
    if(options.op!=='none')for(const r of selected.regions)overlay+=`<rect class="catalog-highlight" data-catalog-mask="${r.mask}" ${box} fill="#d2a843" fill-opacity=".25" mask="url(#catalog-region-${r.mask})"/>`;
    overlay+='</g>';
    // Overlays precede outlines and labels, so the selected region stays legible.
    model.html=defs+overlay+model.html;
    const scale=Math.max(.12,Math.min(1.1,((options.width||900)-40)/(b.maxX-b.minX),((options.height||620)-130)/(b.maxY-b.minY)));
    const font=Math.min(32,Math.max(13,12/scale));
    for(const r of catalog.regions) {
      const p=points.get(r.mask),active=options.op!=='none'&&selected.regions.includes(r);
      model.html+=`<g class="catalog-region-count${active?' active':''}" data-euler-zone="${r.mask}" tabindex="0" role="button" aria-label="${esc(regionName(data,r.mask))}: ${r.count} stored concepts"><title>${esc(regionDescription(data,r.mask))}: ${r.count} stored concepts. Inspect members.</title><rect x="${p.x-font*.9}" y="${p.y-font*.75}" width="${font*1.8}" height="${font*1.5}" rx="${font*.5}"/><text text-anchor="middle" x="${p.x}" y="${p.y+font*.35}" style="font-size:${font}px">${r.count}</text></g>`;
    }
    // Replace the semantic footer in exports with the finite catalog meaning.
    model.html=model.html.replace(/<text class="euler-scale-note"[\s\S]*?<\/text>/g,'');
    const keyFont=Math.min(32,Math.max(14,13/scale)),columns=options.compact?1:2;
    const keys=data.concepts.map((c,i)=>`${String.fromCharCode(65+i)} · ${c.nama}${(data.automatic||[]).some(g=>g.id===c.id)?' [auto]':''} (${catalog.sets[i].count})`);
    const columnWidth=Math.max(190,...keys.map(name=>name.length*keyFont*.55+20));
    const center=(b.minX+b.maxX)/2,startY=b.maxY;
    b.minX=Math.min(b.minX,center-columns*columnWidth/2);b.maxX=Math.max(b.maxX,center+columns*columnWidth/2);
    keys.forEach((name,i)=>{
      const c=data.concepts[i],x=center-columns*columnWidth/2+(i%columns)*columnWidth+10,y=startY+Math.floor(i/columns)*keyFont*1.8;
      model.html+=`<g class="catalog-set-key" data-euler-inspect="${c.id}" role="button" tabindex="0" aria-label="Inspect ${esc(c.nama)}"><title>${esc(c.nama)}: ${catalog.sets[i].count} stored concepts</title><text x="${x}" y="${y}" fill="${window.ConceptuumEuler.color(c.id,options.ids||[])}" style="font-size:${keyFont}px">${esc(name)}</text></g>`;
    });
    b.maxY+=Math.ceil(keys.length/columns)*keyFont*1.8+24;
    model.html+=`<text class="euler-scale-note" text-anchor="middle"><tspan x="${(b.minX+b.maxX)/2}" y="${b.maxY-20}">Catalog membership · counts are stored concepts</tspan><tspan x="${(b.minX+b.maxX)/2}" y="${b.maxY-7}">Hatching: no members · areas are illustrative</tspan></text>`;
    model.notice+=' Hatching marks empty catalog regions; areas are illustrative.';
    return model;
  }
  return {operations,demos,evaluate,regionName,regionDescription,decorate,regionPoints};
})();
