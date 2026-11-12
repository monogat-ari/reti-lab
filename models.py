from dataclasses import dataclass, asdict
from ipaddress import IPv4Network, IPv4Address
import random

@dataclass
class Subnet:
    cidr: str
    min_ip: int
    @property
    def network(self): return IPv4Network(self.cidr)
    @property
    def label(self): return f'{self.cidr}, {self.network.broadcast_address}'
    @staticmethod
    def prefix(hosts): return 32 - (hosts + 1).bit_length()

@dataclass
class Node:
    id: str
    kind: str
    area: str
    x: int
    y: int
    min_ip: int = 0
    cidr: str = ''

@dataclass
class Topology:
    nodes: list
    edges: list
    subnets: dict
    rows: list
    choices: list
    def public(self, mode):
        nodes = [asdict(n) for n in self.nodes]
        if mode == 'A':
            for n in nodes: n['cidr'] = ''
        return dict(nodes=nodes, edges=self.edges, choices=self.choices, **getattr(self,'details',{}),
                    rows=[{**r, 'fields': [{k:v for k,v in f.items() if k != 'answer'} for f in r['fields']]} for r in self.rows] if mode == 'B' else [])

def generate(seed):
    from detailed import enrich, options
    rng = random.Random(seed)
    nodes = [Node('Internet','Internet','Internet',80,80), Node('F1','Firewall','GREEN',340,80)]
    edges = [dict(a='Internet',b='F1',label='tap0 192.0.2.1 ↔ e0 192.0.2.2 · 192.0.2.0/30')]
    subnets = {}; cursor = int(IPv4Address(f'10.{rng.randrange(1,240)}.0.0'))
    rows = []
    structural = ['iptables','-F','-X','-P','-A','-t','-p','-i','-o','-j','-s','-d','--sport','--dport','-m','state','--state','ESTABLISHED,RELATED','INPUT','OUTPUT','FORWARD','PREROUTING','ACCEPT','DROP','DNAT','nat','tcp','udp','--to-destination','ip','route','add','via','default']
    def row(title, tokens):
        fields = []
        for token in tokens:
            manual = isinstance(token, tuple)
            answer, label = token if manual else (token, 'Comando / opzione')
            fields.append(dict(type='text' if manual else 'select', answer=answer, label=label, options=[] if manual else options(answer,rng)))
        rows.append(dict(id=str(len(rows)), title=title, fields=fields))
    row('Elimina le regole della tabella filter', ['iptables','-F'])
    row('Elimina le catene utente della tabella filter', ['iptables','-X'])
    for chain in ['INPUT','OUTPUT','FORWARD']: row('Policy predefinita '+chain,['iptables','-P',chain,'DROP'])
    destinations = []
    for index, area in enumerate(['GREEN','DMZ','RED']):
        x = 170 + index*370
        router = 'F1' if index == 0 else 'R'+str(index)
        if index:
            transit = f'172.20.{index}.0/30'
            nodes.append(Node(router,'Router',area,x,210))
            edges.append(dict(a='F1',b=router,label=f'e{index+1} 172.20.{index}.1 ↔ e0 172.20.{index}.2 · {transit}'))
        cursor = ((cursor+4095)//4096)*4096
        count = 1 if index == 0 else 2
        for j in range(count):
            hosts = rng.choice([60,70,122,222,244,300,371,511])
            prefix = Subnet.prefix(hosts); size = 2**(32-prefix)
            cursor = ((cursor+size-1)//size)*size
            subnet = Subnet(str(IPv4Network((cursor,prefix))), hosts); cursor += size
            cd = 'CD'+str(len(subnets)+1); subnets[cd] = subnet
            xx = x + (j*150-70 if count == 2 else 0)
            nodes.append(Node(cd,'Switch',area,xx,370,hosts,subnet.cidr))
            pc = 'PC'+str(len(subnets)); ip = str(subnet.network.network_address+2)
            nodes.append(Node(pc,'PC',area,xx,490,0,ip))
            edges.extend([dict(a=router,b=cd,label=f'e{j+1} · {subnet.network.network_address+1}'),dict(a=cd,b=pc,label='e0 ↔ eth0')])
            if index: row(f'Rotta F1 verso {area} / {cd}', ['ip','route','add',(subnet.cidr,'Subnet destinazione'),'via',(f'172.20.{index}.2','Gateway')])
            if area == 'DMZ': destinations.append(ip)
    row('Rotta F1 verso Internet',['ip','route','add','default','via',('192.0.2.1','Gateway')])
    row('Consenti SSH da Internet a R2 (172.20.2.2)', ['iptables','-A','FORWARD','-p','tcp','--dport',('22','Porta'),'-i',('e0','Interfaccia ingresso'),'-o',('e3','Interfaccia uscita'),'-d',('172.20.2.2','IP destinazione'),'-j','ACCEPT'])
    row('Consenti le risposte SSH da R2', ['iptables','-A','FORWARD','-p','tcp','--sport',('22','Porta'),'-i',('e3','Interfaccia ingresso'),'-o',('e0','Interfaccia uscita'),'-s',('172.20.2.2','IP sorgente'),'-m','state','--state','ESTABLISHED,RELATED','-j','ACCEPT'])
    server = destinations[0]
    row(f'DNAT HTTP da Internet verso {server}', ['iptables','-t','nat','-A','PREROUTING','-i',('e0','Interfaccia ingresso'),'-p','tcp','--dport',('80','Porta'),'-j','DNAT','--to-destination',(server,'IP destinazione')])
    row('Consenti HTTP dopo DNAT',['iptables','-A','FORWARD','-p','tcp','--dport',('80','Porta'),'-i',('e0','Interfaccia ingresso'),'-o',('e2','Interfaccia uscita'),'-d',(server,'IP destinazione'),'-j','ACCEPT'])
    row('Consenti risposte HTTP dalla DMZ',['iptables','-A','FORWARD','-p','tcp','--sport',('80','Porta'),'-i',('e2','Interfaccia ingresso'),'-o',('e0','Interfaccia uscita'),'-s',(server,'IP sorgente'),'-m','state','--state','ESTABLISHED,RELATED','-j','ACCEPT'])
    choices = list(dict.fromkeys(s.label for s in subnets.values()))
    choices += [Subnet(f'10.250.{i}.0/24',0).label for i in range(3)]
    rng.shuffle(choices)
    t=enrich(Topology(nodes,edges,subnets,rows,choices))
    from professor import build_rows
    t.rows=build_rows(t,seed)
    return t
