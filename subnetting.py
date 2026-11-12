"""Esercizio gerarchico: LAN e aggregati dei router, transiti esclusi."""
import random
from ipaddress import IPv4Network
from models import Node, Subnet

def generate_subnetting(seed):
    rng = random.Random(seed)
    nodes = [Node('Internet','Internet','',55,250), Node('TAP','Transit','',145,250),
             Node('F1','Firewall','',260,250), Node('CD2','Transit','',500,320),
             Node('F2','Firewall','',750,320), Node('CD3','Transit','',500,165),
             Node('R1','Router','RED',750,120), Node('CD4','Transit','',920,320),
             Node('R2','Router','YELLOW',1120,320), Node('CD7','Transit','',750,490),
             Node('R3','Router','DMZ',500,490)]
    edges=[]; targets=[]; solutions={}
    def edge(a,b,ia='',ib=''):
        edges.append(dict(a=a,b=b,ia=ia,ib=ib))
    edge('Internet','TAP','tap0');edge('TAP','F1','','eth0')
    edge('F1','CD2','eth2');edge('CD2','F2','','eth2')
    edge('F1','CD3','eth3');edge('CD3','R1','','eth0')
    edge('F2','CD4','eth0');edge('CD4','R2','','eth0')
    edge('F2','CD7','eth1');edge('CD7','R3','','eth0')
    octet=rng.randrange(1,240)
    groups=[('R2','YELLOW',0,[(900,600),(1120,600),(1340,600)]),
            ('R3','DMZ',16,[(390,670),(630,670)]),
            ('R1','RED',24,[(1000,100),(1260,190)]),
            ('F1','GREEN',32,[(260,435)])]
    # Include every prefix from /27 to /22, with two extra distinct requirements.
    capacities = (32, 64, 128, 256, 512, 1024)
    requirements = [rng.randint(size // 2 - 1, size - 2) for size in capacities]
    remaining = [h for h in range(capacities[0] // 2 - 1, capacities[-1] - 1) if h not in requirements]
    requirements.extend(rng.sample(remaining, 2))
    rng.shuffle(requirements)
    requirements_iter = iter(requirements)
    cdnum=8; pcnum=1
    for router,area,offset,positions in groups:
        hosts=[next(requirements_iter) for _ in positions]
        sizes=[2**(32-Subnet.prefix(h)) for h in hosts]
        total=sum(sizes); blocksize=1<<(total-1).bit_length()
        parent=IPv4Network(f'10.{octet}.{offset}.0/{32-(blocksize.bit_length()-1)}')
        cursor=int(parent.network_address); allocated={}
        for i in sorted(range(len(hosts)), key=lambda i:-sizes[i]):
            allocated[i]=Subnet(str(IPv4Network((cursor,Subnet.prefix(hosts[i])))),hosts[i]);cursor+=sizes[i]
        children=[]
        for i,(x,y) in enumerate(positions):
            cd=f'CD{cdnum}';cdnum+=1;children.append(cd)
            nodes.append(Node(cd,'Switch',area,x,y,hosts[i]))
            edge(router,cd,f'eth{i+1}')
            targets.append(dict(id=cd,x=x,y=y+20,kind='lan',area=area,min_ip=hosts[i]))
            solutions[cd]=allocated[i]
            for j in range(2 if area in ['GREEN','DMZ'] else 1):
                pc=f'S{pcnum}' if area=='DMZ' else f'PC{pcnum}';pcnum+=1
                nodes.append(Node(pc,'Server' if area=='DMZ' else 'PC',area,x+(j*100-50 if area in ['GREEN','DMZ'] else 0),y+140))
                edge(cd,pc,'','eth0')
        if router!='F1':
            n=next(n for n in nodes if n.id==router)
            targets.append(dict(id=router,x=n.x,y=n.y+35,kind='aggregate',area=area,children=children))
            solutions[router]=Subnet(str(parent),0)
    choices=list(dict.fromkeys(s.label for s in solutions.values()))
    for s in list(solutions.values())[:5]:
        # Distrattori: dimensione errata o broadcast non coerente.
        choices.append(f'{s.cidr}, {s.network.broadcast_address-1}')
        choices.append(Subnet(str(s.network.supernet()),0).label)
    choices=list(dict.fromkeys(choices));rng.shuffle(choices)
    public = dict(nodes=[vars(n) for n in nodes],edges=edges,targets=targets,choices=choices,rows=[])
    reshape(public, rng)
    return public,solutions

def check_subnetting(public, solutions, answers):
    parsed={};results={}
    for target in public['targets']:
        key=target['id'];value=answers.get(key,'')
        try:
            net,bc=value.split(',');net=IPv4Network(net.strip())
            if value not in public['choices'] or str(net.broadcast_address)!=bc.strip(): raise ValueError()
            parsed[key]=net
        except (ValueError,AttributeError): pass
    lans=[t for t in public['targets'] if t['kind']=='lan']
    for t in public['targets']:
        key=t['id'];net=parsed.get(key);ok=net is not None
        if t['kind']=='lan':
            ok=ok and net.prefixlen==Subnet.prefix(t['min_ip'])
            ok=ok and not any(other['id']!=key and other['id'] in parsed and net.overlaps(parsed[other['id']]) for other in lans)
            msg=f"Richiesta /{Subnet.prefix(t['min_ip'])}, broadcast coerente e LAN non sovrapposte."
        else:
            children=[parsed.get(c) for c in t['children']]
            ok=ok and all(children)
            if ok:
                low=min(int(c.network_address) for c in children);high=max(int(c.broadcast_address) for c in children)
                prefix=32-(low^high).bit_length()
                ok=net==IPv4Network((low,prefix),strict=False)
            msg='Lâ€™aggregato deve essere il piÃ¹ piccolo blocco CIDR che contiene le LAN assegnate a questo router.'
        results[key]=dict(correct=bool(ok),message='Corretto' if ok else msg)
    return results


def reshape(public, rng):
    """Random rooted device tree and tidy layout; addressing is independent."""
    nodes={n['id']:n for n in public['nodes'] if n['kind'] not in ('Transit','PC','Server')}
    children={key:[] for key in nodes}
    order=['F2','R1','R2','R3'];rng.shuffle(order)
    connected=['F1']
    # Different depths and branching factors, not just shuffled coordinates.
    for device in order:
        parent=rng.choice(connected)
        children[parent].append(device);connected.append(device)
    children['Internet']=['F1']
    areas=['GREEN','DMZ','RED','YELLOW'];rng.shuffle(areas)
    owners=['F1','R1','R2','R3']
    for owner,area in zip(owners,areas):
        nodes[owner]['area']=area
        old=[e['b'] for e in public['edges'] if e['a']==owner and e['b'] in nodes and nodes[e['b']]['kind']=='Switch']
        children[owner].extend(old)
        for cd in old:
            nodes[cd]['area']=area
            for target in public['targets']:
                if target['id']==cd or target['id']==owner: target['area']=area
            count=rng.randint(1,3)
            for j in range(count):
                name=('S' if area=='DMZ' else 'PC')+cd[2:]+'_'+str(j+1)
                nodes[name]=dict(id=name,kind='Server' if area=='DMZ' else 'PC',area=area,x=0,y=0,min_ip=0,cidr='')
                children[name]=[];children[cd].append(name)
    for group in children.values(): rng.shuffle(group)
    widths={}
    def measure(key):
        widths[key]=max(240 if nodes[key]['kind']=='Switch' else 100,sum(measure(c) for c in children[key]))
        return widths[key]
    measure('Internet')
    def place(key,left,depth):
        node=nodes[key];node['x']=left+widths[key]/2;node['y']=80+depth*210
        offset=left+(widths[key]-sum(widths[c] for c in children[key]))/2
        for c in children[key]:place(c,offset,depth+1);offset+=widths[c]
    place('Internet',30,0)
    # Mirror complete branches to vary their visual position without overlaps.
    if rng.choice([True,False]):
        for n in nodes.values(): n['x']=widths['Internet']+60-n['x']
    edges=[];transits=[]
    for parent,group in children.items():
        for i,child in enumerate(group):
            a,b=nodes[parent],nodes[child]
            ia='tap0' if parent=='Internet' else ('' if a['kind']=='Switch' else f'eth{i+1}')
            ib='eth0' if b['kind']!='Switch' else ''
            if a['kind'] in ('Internet','Router','Firewall') and b['kind'] in ('Router','Firewall'):
                name='TAP' if parent=='Internet' else 'T'+str(len(transits))
                transits.append(dict(id=name,kind='Transit',area='',x=(a['x']+b['x'])/2,y=(a['y']+b['y'])/2,min_ip=0,cidr=''))
                edges.extend([dict(a=parent,b=name,ia=ia,ib=''),dict(a=name,b=child,ia='',ib=ib)])
            else: edges.append(dict(a=parent,b=child,ia=ia,ib=ib))
    for target in public['targets']:
        node=nodes[target['id']];target['x']=node['x'];target['y']=node['y']+(20 if target['kind']=='lan' else 35)
    def signature(key):
        return nodes[key]['kind']+'('+','.join(sorted(signature(c) for c in children[key]))+')'
    import hashlib
    public['shape']=hashlib.sha256(signature('Internet').encode()).hexdigest()
    counts={'PC':0,'Server':0}
    rename={}
    for node in nodes.values():
        if node['kind'] in counts:
            counts[node['kind']]+=1
            rename[node['id']]=('PC' if node['kind']=='PC' else 'S')+str(counts[node['kind']])
    for node in nodes.values(): node['id']=rename.get(node['id'],node['id'])
    for edge in edges:
        edge['a']=rename.get(edge['a'],edge['a']);edge['b']=rename.get(edge['b'],edge['b'])
    public['nodes']=list(nodes.values())+transits;public['edges']=edges
    public['width']=widths['Internet']+60
    public['height']=max(n['y'] for n in nodes.values())+100
