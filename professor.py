"""Exercise templates transcribed from the supplied F1.sh, F2.sh and tap.sh.

Only active iptables examples are used. Addresses follow the generated graph;
the files are never executed. Each command is an independent fill-in exercise.
"""
import random
from ipaddress import IPv4Network
from detailed import options

def build_rows(t, seed):
    rng=random.Random(seed ^ 0xF1F2)
    rows=[]
    nets={a['name']:a['network'] for a in t.details['areas']}
    green,dmz,red=(nets[a] for a in ('GREEN','DMZ','RED'))
    hosts=[n.cidr for n in t.nodes if n.kind=='Server']
    manual=lambda value,label:(value,label)
    ip=lambda value:manual(value,'IP / subnet')
    iface=lambda value:manual(value,'Interfaccia')
    port=lambda value:manual(str(value),'Porta')
    chain_groups=[['greenAll','allGreen','inetDMZ','DMZinet'],['DMZred','redDMZ','greenAll','allGreen']]
    extra={'-N':['-N','-X','-F','-A'],
           'NEW,ESTABLISHED,RELATED':['NEW,ESTABLISHED,RELATED','ESTABLISHED,RELATED','NEW','INVALID'],
           'POSTROUTING':['POSTROUTING','PREROUTING','OUTPUT'],
           'MASQUERADE':['MASQUERADE','SNAT','DNAT','ACCEPT'],
           '--to':['--to','--to-source','--to-ports'],
           'tunctl':['tunctl','ifconfig','ip'],
           'ifconfig':['ifconfig','tunctl','ip'],
           '-g':['-g','-u','-t'],
           'netdev':['netdev','root','users'],
           'netmask':['netmask','broadcast','pointopoint'],
           'broadcast':['broadcast','netmask','pointopoint'],
           'up':['up','down','promisc'],
           'sysctl':['sysctl','ifconfig','route'],
           '-w':['-w','-a','-p'],
           'net.ipv4.ip_forward=1':['net.ipv4.ip_forward=1','net.ipv4.ip_forward=0','net.ipv4.conf.all.forwarding=0'],
           '-net':['-net','-host','default'],
           'gw':['gw','dev','netmask'],
           'dev':['dev','gw','netmask']}
    def row(device,section,title,tokens):
        fields=[]
        for token in tokens:
            is_text=isinstance(token,tuple)
            answer,label=token if is_text else (token,'Comando / opzione')
            pool=[]
            if not is_text:
                pool=next((list(g) for g in chain_groups if answer in g),None)
                if pool is None:pool=list(extra[answer]) if answer in extra else options(answer,rng)
                if tokens[0]=='tunctl' and answer=='-t':pool=['-t','-d','-g']
                rng.shuffle(pool)
            fields.append(dict(type='text' if is_text else 'select',answer=answer,label=label,options=pool))
        rows.append(dict(id=str(len(rows)),device=device,section=section,title=title,fields=fields))
    def add(device,section,title,tail):row(device,section,title,['iptables']+tail)
    def init(device):
        add(device,'Pulizia del firewall','Eliminazione di tutte le regole',['-F'])
        add(device,'Pulizia del firewall','Eliminazione di tutte le catene utente',['-X'])
        for chain in ['INPUT','OUTPUT','FORWARD']:
            add(device,'Setting delle policy di default',chain,['-P',chain,'DROP'])
    tap=IPv4Network(t.details['metadata']['CD TAP']['network'])
    row('Host TAP','Creazione interfaccia TAP','Crea tap0 per il gruppo netdev',['tunctl','-g','netdev','-t',iface('tap0')])
    row('Host TAP','Creazione interfaccia TAP','Assegna il primo IP utilizzabile del CD TAP',['ifconfig',iface('tap0'),ip(str(tap.network_address+1))])
    row('Host TAP','Creazione interfaccia TAP','Imposta la maschera del CD TAP',['ifconfig',iface('tap0'),'netmask',manual(str(tap.netmask),'Netmask')])
    row('Host TAP','Creazione interfaccia TAP','Imposta il broadcast del CD TAP',['ifconfig',iface('tap0'),'broadcast',ip(str(tap.broadcast_address))])
    row('Host TAP','Creazione interfaccia TAP','Attiva tap0',['ifconfig',iface('tap0'),'up'])
    row('Host TAP','Forwarding IPv4','Abilita inoltro IPv4 sull’host',['sysctl','-w','net.ipv4.ip_forward=1'])
    init('F1')
    add('F1','Abilitare SSH in F1','Richiesta da CD TAP',['-A','INPUT','-p','tcp','--dport',port(22),'-s',ip('192.0.2.0/30'),'-i',iface('eth0'),'-j','ACCEPT'])
    add('F1','Abilitare SSH in F1','Risposta verso CD TAP',['-A','OUTPUT','-p','tcp','--sport',port(22),'-d',ip('192.0.2.0/30'),'-o',iface('eth0'),'-j','ACCEPT'])
    for c in chain_groups[0]:add('F1','Creazione delle sottocatene',c,['-N',c])
    for name,tail in [
        ('greenAll',['-s',ip(green),'-i',iface('eth1')]),
        ('allGreen',['-d',ip(green),'-o',iface('eth1')]),
        ('inetDMZ',['-i',iface('eth0'),'-o',iface('eth2'),'-d',ip(dmz)]),
        ('DMZinet',['-o',iface('eth0'),'-i',iface('eth2'),'-s',ip(dmz)])]:
        add('F1','Aggancio delle sottocatene',name,['-A','FORWARD']+tail+['-j',name])
    for name in chain_groups[0]:
        state='NEW,ESTABLISHED,RELATED' if name in ['greenAll','inetDMZ'] else 'ESTABLISHED,RELATED'
        add('F1','Applicazione delle regole',name,['-A',name,'-m','state','--state',state,'-j','ACCEPT'])
    add('F1','Abilitare SSH su F2 (parte 1)','Andata da CD TAP a F2',['-A','FORWARD','-p','tcp','--dport',port(22),'-i',iface('eth0'),'-o',iface('eth2'),'-d',ip('172.20.2.2'),'-j','ACCEPT'])
    add('F1','Abilitare SSH su F2 (parte 1)','Risposta da F2 a CD TAP',['-A','FORWARD','-p','tcp','--sport',port(22),'-i',iface('eth2'),'-o',iface('eth0'),'-s',ip('172.20.2.2'),'-m','state','--state','ESTABLISHED,RELATED','-j','ACCEPT'])
    for source,dest,flag in [(80,hosts[1],'--to-destination'),(4443,hosts[0]+':443','--to'),(2525,hosts[2],'--to')]:
        add('F1','Natting / DNAT',f'Portforwarding della porta {source} su {dest}',['-t','nat','-A','PREROUTING','-i',iface('eth0'),'-p','tcp','--dport',port(source),'-j','DNAT',flag,manual(dest,'IP destinazione[:porta]')])
    init('F2')
    add('F2','Abilitare SSH in F2 (parte 2)','Richiesta in ingresso',['-A','INPUT','-p','tcp','-i',iface('eth0'),'--dport',port(22),'-j','ACCEPT'])
    add('F2','Abilitare SSH in F2 (parte 2)','Risposta in uscita',['-A','OUTPUT','-p','tcp','-o',iface('eth0'),'--sport',port(22),'-j','ACCEPT'])
    for c in ['greenAll','allGreen','DMZred','redDMZ']:add('F2','Creazione delle sottocatene',c,['-N',c])
    for name,tail in [
        ('greenAll',['-s',ip(green),'-i',iface('eth0'),'-o',iface('eth1')]),
        ('allGreen',['-d',ip(green),'-i',iface('eth1'),'-o',iface('eth0')]),
        ('DMZred',['-i',iface('eth0'),'-o',iface('eth1'),'-s',ip(dmz),'-d',ip(red)]),
        ('redDMZ',['-o',iface('eth0'),'-i',iface('eth1'),'-d',ip(dmz),'-s',ip(red)])]:
        add('F2','Aggancio delle sottocatene',name,['-A','FORWARD']+tail+['-j',name])
    for name in ['greenAll','allGreen','DMZred','redDMZ']:
        tail=['-m','state','--state','ESTABLISHED,RELATED'] if name in ['allGreen','redDMZ'] else []
        add('F2','Applicazione delle regole',name,['-A',name]+tail+['-j','ACCEPT'])
    for tail in [['-t','nat','-F'],['-t','nat','-X'],['-F'],['-X']]:
        add('Host TAP','Pulizia del firewall','Tabella nat' if 'nat' in tail else 'Tabella filter',tail)
    add('Host TAP','Accesso a Internet','Masquerading: wlan0 e la scheda esterna dell’host',['-t','nat','-A','POSTROUTING','-o',iface('wlan0'),'-j','MASQUERADE'])
    add('Host TAP','Accesso a Internet','Forwarding dal TAP',['-A','FORWARD','-i',iface('tap0'),'-j','ACCEPT'])
    # Legacy route syntax from tap.sh. Directly connected networks require no
    # static gateway route; every listed gateway is an adjacent L3 interface.
    def route(device,title,dest,gateway,interface):
        tokens=['route','add']+(['default'] if dest=='default' else ['-net',ip(dest)])
        tokens+=['gw',ip(gateway),'dev',iface(interface)]
        row(device,'Rotte statiche',title,tokens)
    trans={key:t.details['metadata'][key]['network'] for key in ['CD2','CD4','CD5']}
    for area,network in nets.items():
        route('Host TAP',f'Raggiungi {area} attraverso F1',network,str(tap.network_address+2),'tap0')
    for cd,network in trans.items():
        route('Host TAP',f'Raggiungi il transito {cd} attraverso F1',network,str(tap.network_address+2),'tap0')
    for area in ['DMZ','RED']:route('F1',f'Raggiungi {area} attraverso R1',nets[area],'172.20.1.2','eth2')
    for cd in ['CD4','CD5']:route('F1',f'Raggiungi {cd} (gestione dei dispositivi)',trans[cd],'172.20.1.2','eth2')
    route('F1','Rotta predefinita verso Internet / host TAP','default',str(tap.network_address+1),'eth0')
    route('R1','Raggiungi GREEN attraverso F1',green,'172.20.1.1','eth0')
    route('R1','Raggiungi RED attraverso F2',red,'172.20.2.2','eth3')
    route('R1','Raggiungi CD5 attraverso F2',trans['CD5'],'172.20.2.2','eth3')
    route('R1','Rotta predefinita e ritorno verso Internet attraverso F1','default','172.20.1.1','eth0')
    for area in ['GREEN','DMZ']:route('F2',f'Raggiungi {area} attraverso R1',nets[area],'172.20.2.1','eth0')
    route('F2','Raggiungi RED attraverso R2',red,'172.20.3.2','eth1')
    route('F2','Raggiungi CD2 attraverso R1',trans['CD2'],'172.20.2.1','eth0')
    route('F2','Rotta predefinita e ritorno verso Internet attraverso R1','default','172.20.2.1','eth0')
    for area in ['GREEN','DMZ']:route('R2',f'Raggiungi {area} attraverso F2',nets[area],'172.20.3.1','eth0')
    for cd in ['CD2','CD4']:route('R2',f'Raggiungi {cd} attraverso F2',trans[cd],'172.20.3.1','eth0')
    route('R2','Rotta predefinita e ritorno verso Internet attraverso F2','default','172.20.3.1','eth0')
    descriptions={'greenAll':'GREEN verso le altre reti','allGreen':'altre reti verso GREEN','inetDMZ':'Internet verso DMZ','DMZinet':'DMZ verso Internet','DMZred':'DMZ verso RED','redDMZ':'RED verso DMZ'}
    for r in rows:
        if r['section']=='Aggancio delle sottocatene':r['title']+=' - '+descriptions[r['title']]
    return rows
