from ipaddress import IPv4Network
from models import Node

def enrich(t):
    """Topology F1--R1--F2--R2, with all interface and subnet data."""
    nodes=[Node('Internet','Internet','',90,180),Node('F1','Firewall','GREEN',350,180),
           Node('R1','Router','DMZ',350,620),Node('F2','Firewall','',830,620),Node('R2','Router','RED',1200,620)]
    edges=[]; metadata={};areas=[]
    def info(cidr):
        n=IPv4Network(cidr)
        return dict(network=str(n),netmask=str(n.netmask),broadcast=str(n.broadcast_address))
    def link(a,b,ia,ib):edges.append(dict(a=a,b=b,ia=ia,ib=ib))
    def transit(name,cidr,a,b,ia,ib,x,y):
        n=IPv4Network(cidr);nodes.append(Node(name,'Transit','',x,y))
        metadata[name]=info(cidr)
        link(a,name,f'{ia}  {n.network_address+1}','e0')
        link(name,b,'e1',f'{ib}  {n.network_address+2}')
    transit('CD TAP','192.0.2.0/30','Internet','F1','tap0','e0',220,180)
    transit('CD2','172.20.1.0/30','F1','R1','e2','e0',350,410)
    transit('CD4','172.20.2.0/30','R1','F2','e3','e0',600,620)
    transit('CD5','172.20.3.0/30','F2','R2','e1','e0',1010,620)
    old=list(t.subnets.values());t.subnets={};pc=1;server=1
    groups=[('GREEN','F1',[old[0]],[(700,180)],(300,40,650,290)),
            ('DMZ','R1',old[1:3],[(190,810),(510,810)],(40,500,650,550)),
            ('RED','R2',old[3:5],[(1050,810),(1370,810)],(900,500,650,550))]
    for area,owner,subnets,positions,box in groups:
        low=min(int(s.network.network_address) for s in subnets);high=max(int(s.network.broadcast_address) for s in subnets)
        summary=IPv4Network((low,32-(low^high).bit_length()),strict=False)
        areas.append(dict(name=area,box=box,**info(str(summary))))
        for j,(s,(x,y)) in enumerate(zip(subnets,positions)):
            cd='CD1' if area=='GREEN' else ('CD'+str(8+j) if area=='DMZ' else 'CD'+str(6+j))
            t.subnets[cd]=s;nodes.append(Node(cd,'Switch',area,x,y,s.min_ip,s.cidr));metadata[cd]=info(s.cidr)
            link(owner,cd,f'e{j+1}  {s.network.network_address+1}','e0')
            for k in range(2):
                name=f'S{server}' if area=='DMZ' else f'PC{pc}'
                if area=='DMZ':server+=1
                else:pc+=1
                nx=x+(-65 if k==0 else 65);ny=y+(90 if area=='GREEN' else 170)
                ip=str(s.network.network_address+k+2)
                nodes.append(Node(name,'Server' if area=='DMZ' else 'PC',area,nx,ny,0,ip))
                link(cd,name,f'e{k+1}',f'eth0  {ip}')
    t.nodes=nodes;t.edges=edges
    # The professor's Linux interface naming applies to L3 devices, not switches.
    by_id={n.id:n for n in nodes}
    import re
    for e in edges:
        for endpoint,label in [('a','ia'),('b','ib')]:
            if by_id[e[endpoint]].kind in ['Router','Firewall']:
                e[label]=re.sub(r'^e(\d+)',r'eth\1',e[label])
    t.details=dict(metadata=metadata,areas=areas,width=1600,height=1100)
    for row in t.rows:
        row['title']=row['title'].replace('R2','F2')
        for field in row['fields']:
            if field['answer']=='e3':field['answer']='e2'
        if row['title'].startswith('Rotta F1 verso') and 'Internet' not in row['title']:
            row['fields'][-1]['answer']='172.20.1.2'
            cidr=row['fields'][3]['answer']
            cd=next(k for k,s in t.subnets.items() if s.cidr==cidr)
            row['title']=row['title'].split(' / ')[0]+' / '+cd
    return t

def options(answer, rng):
    groups=[['iptables','ip','nft','route'],['-F','-X','-Z','-A'],['-P','-A','-I','-D'],
            ['-t','-p','-m','-j'],['-i','-o','-s','-d'],['--sport','--dport','--sports','--dports'],
            ['INPUT','OUTPUT','FORWARD','PREROUTING'],['ACCEPT','DROP','REJECT','DNAT'],
            ['nat','filter','mangle','raw'],['tcp','udp','icmp'],['state','conntrack','multiport'],
            ['--state','--ctstate','--tcp-flags'],['ESTABLISHED,RELATED','NEW','INVALID','ESTABLISHED'],
            ['--to-destination','--to-source','--to-ports'],['route','address','link'],
            ['add','del','replace'],['via','dev','src'],['default','local','broadcast']]
    pool=['route','address','link'] if answer=='route' else next(g for g in groups if answer in g)
    result=list(pool);rng.shuffle(result);return result
