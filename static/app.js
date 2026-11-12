let mode='A', topology, selected=null;
const $=s=>document.querySelector(s);
function el(tag,text,cls){const e=document.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e}
function svg(tag,attrs,text){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text)e.textContent=text;$('#graph').append(e);return e}
async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw Error(j.error||'Errore del server');return j}
function render(){document.body.classList.toggle('subnetting',mode==='A');draw();$('#exercise').replaceChildren();$('#choices').replaceChildren();$('#status').textContent='';selected=null;$('#title').textContent=mode==='A'?'Configurazioni disponibili':'Regole nello stile del professore';$('#instructions').textContent=mode==='A'?'Trascina una configurazione nella casella del grafo oppure selezionala e fai clic sulla casella. Sui CD assegna la subnet minima per minIP; sotto i router assegna il più piccolo aggregato delle rispettive LAN. I transiti non hanno caselle. Canc/Backspace svuota la casella selezionata.':'Segui l\'ordine dei file F1.sh, F2.sh e tap.sh, con gli indirizzi della topologia. Ogni sezione indica il dispositivo su cui scrivere la regola. I nomi delle sottocatene sono quelli del professore. Comandi, flag e valori strutturali sono menu; IP, subnet, porte e interfacce si scrivono a mano. Configurazione TAP e rotte si completano nelle rispettive sezioni. Per il routing usa route add -net SUBNET gw GATEWAY dev INTERFACCIA; per Internet usa route add default. Il gateway deve essere adiacente. Le reti direttamente connesse non richiedono rotte statiche. Si assume il forwarding attivo su router e firewall e il gateway predefinito configurato sui PC. Host TAP usa tap0 verso la rete e wlan0 verso Internet. Le righe sono esercizi indipendenti, non uno script da eseguire in sequenza. Le regole non vengono eseguite.';
if(mode==='A'){topology.choices.forEach(c=>{const b=el('button',c);b.type='button';b.draggable=true;b.ondragstart=e=>{selected=c;e.dataTransfer.setData('text/plain',c)};b.onclick=()=>{selected=c;$('#choices').querySelectorAll('button').forEach(x=>x.classList.toggle('selected',x===b))};$('#choices').append(b)});}else{let previousGroup='';topology.rows.forEach(r=>{const group=(r.device||'F1')+' / '+(r.section||'Comandi');if(group!==previousGroup){$('#exercise').append(el('h3',group,'command-section'));previousGroup=group}const row=el('div',null,'command');row.dataset.id=r.id;row.append(el('label',r.title));const fields=el('div',null,'fields');r.fields.forEach((f,i)=>{const c=el(f.type==='select'?'select':'input');c.setAttribute('aria-label',`${r.title}: ${f.label} ${i+1}`);if(f.type==='select'){const blank=new Option('Scegli','');blank.disabled=true;blank.selected=true;c.append(blank);f.options.forEach(o=>c.append(new Option(o,o)));c.onchange=()=>{c.style.width=Math.max(90,c.value.length*8+35)+'px';c.className=''}}else{c.type='text';c.placeholder=f.label;c.autocomplete='off';c.oninput=()=>c.className=''}fields.append(c)});row.append(fields,el('p','','feedback'));$('#exercise').append(row)})}}
async function fresh(){try{$('#new').disabled=true;$('#check').disabled=true;topology=await api('/api/new',{mode});render();$('#check').disabled=false}catch(e){$('#status').textContent=e.message}finally{$('#new').disabled=false}}
$('#new').onclick=fresh;document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));fresh()});$('#exercise').onsubmit=e=>e.preventDefault();$('#check').onclick=async()=>{const data={};document.querySelectorAll('[data-id]').forEach(r=>data[r.dataset.id]=mode==='A'?r.querySelector('button').dataset.value:[...r.querySelectorAll('select,input')].map(e=>e.value));try{const result=await api('/api/check',data);$('#status').textContent=`${result.score} / ${result.total} risposte corrette`;Object.entries(result.results).forEach(([id,r])=>{const row=$(`[data-id="${id}"]`);row.querySelector('.feedback').textContent=r.correct?'✓ Corretto':r.message;if(mode==='A'){const b=row.querySelector('button');b.className=r.correct?'good':'bad';b.title=r.correct?'Corretto':r.message;b.setAttribute('aria-label',id+': '+(r.correct?'Corretto':r.message));}else row.querySelectorAll('select,input').forEach((c,i)=>c.className=r.fields[i]?'good':'bad')})}catch(e){$('#status').textContent=e.message}};

function draw(){
 if(mode==='B'){$('#graph').style.minWidth='850px';$('#graph').setAttribute('viewBox','0 0 1120 560');drawDetailed();return}
 const g=$('#graph');g.replaceChildren();g.setAttribute('viewBox',`0 0 ${topology.width||1460} ${topology.height||880}`);g.style.minWidth='0';g.style.width=Math.round((topology.width||1460)*.75)+'px';g.style.maxHeight='none';
 topology.edges.forEach(e=>{
  const a=topology.nodes.find(n=>n.id===e.a),b=topology.nodes.find(n=>n.id===e.b);
  svg('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:'#71818a','stroke-width':1.7});
  
 });
 topology.nodes.forEach(n=>{
  if(['Switch','Transit'].includes(n.kind))svg('circle',{cx:n.x,cy:n.y,r:13,fill:n.kind==='Transit'?'#cbd9c7':'#9cd866',stroke:'#658c42','stroke-width':2});
  else{
   const glyph={Firewall:'FW',Router:'R',PC:'PC',Server:'SRV',Internet:'NET'}[n.kind];
   svg('rect',{x:n.x-24,y:n.y-24,width:48,height:48,rx:n.kind==='Internet'?24:8,fill:n.kind==='Firewall'?'#bb653b':'#315a6c'});
   svg('text',{x:n.x,y:n.y+9,'text-anchor':'middle',style:'fill:white;font-size:16px;font-weight:bold'},glyph);
  }
  const text=n.kind==='Switch'?`${n.id} (${n.area}) minIP: ${n.min_ip}`:n.id;
  svg('text',{x:n.x,y:n.y+(n.kind==='Switch'?69:n.kind==='Transit'?30:-33),'text-anchor':'middle','font-weight':600},text);
 });
 topology.targets.forEach(t=>{
  const fo=svg('foreignObject',{x:t.x-102,y:t.y,width:204,height:38});
  const wrap=el('div',null,'graph-answer');wrap.dataset.id=t.id;
  const b=el('button',t.kind==='aggregate'?`Aggregato ${t.area}`:'network/maschera, broadcast');b.type='button';b.dataset.value='';b.setAttribute('aria-label',`Assegna subnet a ${t.id}`);
  function assign(value){if(topology.choices.includes(value)){b.dataset.value=value;b.textContent=value;b.className='';wrap.querySelector('.feedback').textContent='';$('#status').textContent='Risposta aggiornata: verifica nuovamente.'}}
  b.onclick=()=>assign(selected);b.ondragover=e=>{e.preventDefault();b.classList.add('drag-over')};b.ondragleave=()=>b.classList.remove('drag-over');b.ondrop=e=>{e.preventDefault();b.classList.remove('drag-over');assign(e.dataTransfer.getData('text/plain'))};
  b.onkeydown=e=>{if(e.key==='Delete'||e.key==='Backspace'){b.dataset.value='';b.textContent='network/maschera, broadcast';b.className=''}};
  wrap.append(b,el('span','','feedback'));fo.append(wrap);
 });
 placeEdgeLabels();
};
fresh();

function drawDetailed(){
 const g=$('#graph');g.replaceChildren();g.style.minWidth='1250px';g.style.width='100%';g.style.maxHeight='none';g.setAttribute('viewBox','0 0 1600 1100');
 const colors={GREEN:'#d7f2df',DMZ:'#fff1ba',RED:'#ffdad3'};
 function text(x,y,label,size=12){svg('text',{x,y,style:`font-size:${size}px`},label)}
 function network(x,y,name,data){
  text(x,y,name,13);text(x,y+17,'Network: '+data.network);text(x,y+34,'Netmask: '+data.netmask);text(x,y+51,'Broadcast: '+data.broadcast);
 }
 topology.areas.forEach(a=>{const [x,y,w,h]=a.box;svg('rect',{x,y,width:w,height:h,rx:8,fill:colors[a.name],stroke:'#9badac'});network(x+14,y+22,'Area '+a.name,a)});
 topology.edges.forEach(e=>{
  const a=topology.nodes.find(n=>n.id===e.a),b=topology.nodes.find(n=>n.id===e.b);
  svg('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:'#647d84','stroke-width':2});

 });
 topology.nodes.forEach(n=>{
  svg('rect',{x:n.x-25,y:n.y-19,width:50,height:38,rx:7,fill:n.kind==='Firewall'?'#b65f32':n.kind==='Switch'||n.kind==='Transit'?'#59888a':'#2a5066'});
  const short={Firewall:'FW',Router:'R',PC:'PC',Server:'SRV',Internet:'NET',Switch:'SW',Transit:'SW'}[n.kind];
  svg('text',{x:n.x,y:n.y+5,'text-anchor':'middle',style:'fill:white;font-size:14px;font-weight:bold'},short);
  svg('text',{x:n.x,y:n.y+37,'text-anchor':'middle','font-weight':700},n.id);
  if(n.kind==='PC'||n.kind==='Server')svg('text',{x:n.x,y:n.y+54,'text-anchor':'middle'},n.cidr);
  if(topology.metadata[n.id]){
   const offset=n.id==='CD2'?55:-80;
   network(n.x+offset,n.id==='CD2'?n.y-30:n.id==='CD5'?n.y-200:n.y-104,n.id,topology.metadata[n.id]);
  }
 });
 placeEdgeLabels();
}

// Reserve node names, answer slots and network information before placing labels.
function placeEdgeLabels(){
 const g=$('#graph');
 const occupied=[...g.querySelectorAll('text,foreignObject,rect,circle')].filter(e=>e.tagName!=='rect'||Number(e.getAttribute('width'))<100).map(e=>{const b=e.getBBox();return {x:b.x-5,y:b.y-5,w:b.width+10,h:b.height+10}});
 const bounds=g.viewBox.baseVal;
 function overlaps(a,b){return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y}
 topology.edges.forEach(edge=>{
  const a=topology.nodes.find(n=>n.id===edge.a),b=topology.nodes.find(n=>n.id===edge.b);
  [[edge.ia,.28],[edge.ib,.72]].forEach(([label,t])=>{
   if(!label)return;
   const px=a.x+(b.x-a.x)*t,py=a.y+(b.y-a.y)*t;
   const e=svg('text',{x:px,y:py,'text-anchor':'middle',class:'edge-label'},label);
   const size=e.getBBox();let chosen=null;
   const offsets=[];
   for(const dy of [-15,20,-35,40,-55,60,-80,85,-110,115])for(const dx of [0,35,-35,70,-70,110,-110,160,-160]) offsets.push([dx,dy]);
   for(const [dx,dy] of offsets){
    const box={x:px+dx-size.width/2-4,y:py+dy-size.height-3,w:size.width+8,h:size.height+6};
    if(box.x<5||box.x+box.w>bounds.width-5||box.y<5||box.y+box.h>bounds.height-5)continue;
    if(!occupied.some(o=>overlaps(box,o))){chosen={box,dx,dy};break}
   }
   if(chosen){e.setAttribute('x',px+chosen.dx);e.setAttribute('y',py+chosen.dy);occupied.push(chosen.box);
    if(Math.abs(chosen.dx)>35||Math.abs(chosen.dy)>40){const leader=svg('line',{x1:px,y1:py,x2:px+chosen.dx,y2:py+chosen.dy-5,stroke:'#b0bfc4','stroke-width':.7,'stroke-dasharray':'2 3'});g.insertBefore(leader,e)}
   }else occupied.push({x:size.x,y:size.y,w:size.width,h:size.height});
  });
 });
}

const graphTools=el('div',null,'graph-tools');
const graphBox=$('.graph');graphBox.before(graphTools);
[['Riduci',.85],['Ingrandisci',1.18],['Adatta alla finestra',0]].forEach(([name,factor])=>{
 const button=el('button',name);button.type='button';button.onclick=()=>{const g=$('#graph');g.style.minWidth='0';g.style.maxHeight='none';g.style.width=factor?Math.max(600,Math.min(3500,g.getBoundingClientRect().width*factor))+'px':'100%'};graphTools.append(button);
});
