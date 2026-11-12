import unittest
from models import generate, Subnet
from app import app
from subnetting import generate_subnetting, check_subnetting

class Tests(unittest.TestCase):
    def test_generation(self):
        for seed in range(100):
            t=generate(seed); nets=[s.network for s in t.subnets.values()]
            for s in t.subnets.values():
                self.assertGreaterEqual(s.network.num_addresses-2,s.min_ip)
                self.assertLess(s.network.num_addresses//2-2,s.min_ip)
            for i,n in enumerate(nets):
                for m in nets[i+1:]: self.assertFalse(n.overlaps(m))
            for r in t.public('B')['rows']:
                for f in r['fields']: self.assertNotIn('answer',f)
    def test_checks(self):
        with app.test_client() as c:
            for mode in ['A','B']:
                self.assertEqual(c.post('/api/new',json={'mode':mode}).status_code,200)
                with c.session_transaction() as s: t=generate(s['seed'])
                answers={k:v.label for k,v in generate_subnetting(s['seed'])[1].items()} if mode=='A' else {r['id']:[f['answer'] for f in r['fields']] for r in t.rows}
                result=c.post('/api/check',json=answers).get_json()
                self.assertEqual(result['score'],result['total'])
                self.assertEqual(c.post('/api/check',json={}).get_json()['score'],0)
    def test_overlap(self):
        with app.test_client() as c:
            c.post('/api/new',json={'mode':'A'})
            with c.session_transaction() as s: t=generate(s['seed'])
            public, solutions=generate_subnetting(s['seed'])
            value=next(iter(solutions.values())).label
            result=c.post('/api/check',json={k:value for k in solutions}).get_json()
            self.assertTrue(all(not result['results'][t['id']]['correct'] for t in public['targets'] if t['kind']=='lan'))

if __name__=='__main__': unittest.main()

class HierarchyTests(unittest.TestCase):
    def test_min_ip_variety(self):
        for seed in range(100):
            public, solutions = generate_subnetting(seed)
            lans = [target for target in public['targets'] if target['kind'] == 'lan']
            requirements = {target['min_ip'] for target in lans}
            self.assertEqual(len(requirements), 8)
            self.assertEqual({Subnet.prefix(value) for value in requirements}, set(range(22, 28)))
            for target in lans:
                network = solutions[target['id']].network
                self.assertGreaterEqual(network.num_addresses - 2, target['min_ip'])
                self.assertLess(network.num_addresses // 2 - 2, target['min_ip'])

    def test_hierarchy(self):
        for seed in range(100):
            public, solutions=generate_subnetting(seed)
            answers={k:v.label for k,v in solutions.items()}
            result=check_subnetting(public,solutions,answers)
            self.assertTrue(all(r['correct'] for r in result.values()))
            self.assertEqual(len(public['targets']),11)
            answers['R1']=answers['R2']
            self.assertFalse(check_subnetting(public,solutions,answers)['R1']['correct'])

class ShapeTests(unittest.TestCase):
    def test_variety_and_connectivity(self):
        shapes=set()
        for seed in range(200):
            public, solutions=generate_subnetting(seed)
            shapes.add(public['shape'])
            ids={n['id'] for n in public['nodes']}
            self.assertEqual(len(ids),len(public['nodes']))
            seen={'Internet'}
            while True:
                updated=seen|{e['b'] for e in public['edges'] if e['a'] in seen}
                if updated==seen: break
                seen=updated
            self.assertEqual(seen,ids)
            self.assertEqual(len(public['edges']),len(ids)-1)
            self.assertTrue(all(r['correct'] for r in check_subnetting(public,solutions,{k:v.label for k,v in solutions.items()}).values()))
        self.assertGreater(len(shapes),190)
    def test_no_consecutive_repeat(self):
        with app.test_client() as c:
            previous=None
            for _ in range(30):
                public=c.post('/api/new',json={'mode':'A'}).get_json()
                self.assertNotEqual(previous,public['shape'])
                previous=public['shape']

class DetailedTests(unittest.TestCase):
    def test_metadata_and_choices(self):
        from ipaddress import IPv4Network
        for seed in range(30):
            t=generate(seed); public=t.public('B')
            self.assertEqual(len(public['metadata']),9)
            self.assertEqual(sum(n.kind=='Firewall' for n in t.nodes),2)
            for data in public['metadata'].values():
                n=IPv4Network(data['network'])
                self.assertEqual(str(n.netmask),data['netmask'])
                self.assertEqual(str(n.broadcast_address),data['broadcast'])
            for r in t.rows:
                for f in r['fields']:
                    if f['type']=='select':
                        self.assertLessEqual(len(f['options']),4)
                        self.assertGreaterEqual(len(f['options']),3)
                        self.assertIn(f['answer'],f['options'])
            for r in t.rows:
                if r['title'].startswith('Rotta F1 verso') and 'Internet' not in r['title']:
                    self.assertEqual(r['fields'][-1]['answer'],'172.20.1.2')

class ProfessorTests(unittest.TestCase):
    def test_professor_templates(self):
        t=generate(42)
        commands=[(r['device'],' '.join(f['answer'] for f in r['fields'])) for r in t.rows]
        self.assertIn(('F1','iptables -A FORWARD -p tcp --dport 22 -i eth0 -o eth2 -d 172.20.2.2 -j ACCEPT'),commands)
        self.assertIn(('F2','iptables -A INPUT -p tcp -i eth0 --dport 22 -j ACCEPT'),commands)
        self.assertIn(('Host TAP','iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE'),commands)
        self.assertIn(('F1','iptables -N inetDMZ'),commands)
        self.assertIn(('F1','iptables -A allGreen -m state --state ESTABLISHED,RELATED -j ACCEPT'),commands)
        self.assertFalse(any('--sport 80 -j DNAT' in c for _,c in commands))
        for e in t.edges:
            for endpoint,label in [('a','ia'),('b','ib')]:
                n=next(n for n in t.nodes if n.id==e[endpoint])
                if n.kind in ['Firewall','Router']:self.assertTrue(e[label].startswith('eth'))

class TapRoutingTests(unittest.TestCase):
    def test_tap_and_route_gateways(self):
        from ipaddress import IPv4Network, IPv4Address
        t=generate(77)
        rows=t.rows
        cmds=[' '.join(f['answer'] for f in r['fields']) for r in rows]
        self.assertIn('tunctl -g netdev -t tap0',cmds)
        self.assertIn('ifconfig tap0 broadcast 192.0.2.3',cmds)
        self.assertIn('sysctl -w net.ipv4.ip_forward=1',cmds)
        adjacent={('Host TAP','tap0'):'192.0.2.0/30',('F1','eth0'):'192.0.2.0/30',('F1','eth2'):'172.20.1.0/30',('R1','eth0'):'172.20.1.0/30',('R1','eth3'):'172.20.2.0/30',('F2','eth0'):'172.20.2.0/30',('F2','eth1'):'172.20.3.0/30',('R2','eth0'):'172.20.3.0/30'}
        routing=[r for r in rows if r['section']=='Rotte statiche']
        self.assertEqual({r['device'] for r in routing},{'Host TAP','F1','R1','F2','R2'})
        for r in routing:
            tokens=[f['answer'] for f in r['fields']]
            gateway=tokens[tokens.index('gw')+1];iface=tokens[-1]
            self.assertIn(IPv4Address(gateway),IPv4Network(adjacent[(r['device'],iface)]))
            self.assertEqual(tokens[-2],'dev')
            self.assertEqual(tokens[:2],['route','add'])
            if tokens[2]=='-net':self.assertNotEqual(tokens[3],adjacent[(r['device'],iface)])
        for r in t.public('B')['rows']:
            self.assertNotIn('route',r)
            for f in r['fields']:self.assertNotIn('answer',f)
