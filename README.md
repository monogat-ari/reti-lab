# reti-lab
Piattaforma didattica per esercitarsi con le reti di calcolatori, con generazione di topologie e correzione automatica degli esercizi di subnetting IPv4, routing e firewall.

Piattaforma didattica locale Flask, Python 3.10 o successivo. Nessun comando di rete viene eseguito sul computer.

## Avvio

Aprire un terminale nella cartella `reti-lab`:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Aprire http://127.0.0.1:5000. Su Windows si puÃ² usare `py` al posto di `python` per creare lâ€™ambiente.

## Modello

`models.py` contiene Subnet, Node, Topology e generate(seed). La topologia connessa varia numero delle LAN, requisiti host e indirizzi; lo scheletro Internetâ€“F1â€“router DMZ/RED resta fisso per produrre esercizi coerenti. Il gateway Ã¨ il primo host, il PC rappresentativo il secondo. minIP include il gateway. I transiti sono /30 e non vengono assegnati nellâ€™esercizio A. Le allocazioni LAN sono allineate e disgiunte. Le opzioni possono essere assegnate a qualunque CD compatibile: il backend verifica capacitÃ  minima, broadcast e assenza di sovrapposizioni, senza imporre unâ€™unica permutazione.

Il formulario B Ã¨ generato da uno schema backend: solo indirizzi, subnet, porte e interfacce sono input testuali. La correzione Ã¨ per campo e richiede lâ€™ordine proposto, non Ã¨ un interprete di tutte le sintassi iptables equivalenti. Routing usa `ip route add ... via ...`: `gw` appartiene alla sintassi legacy `route`. Le regole sono esercizi mirati, non una configurazione completa pronta per una rete reale. Si assumono forwarding e rotte di ritorno giÃ  configurati. Internet Ã¨ simulato tramite indirizzi TEST-NET e TAP.

Lo stato Ã¨ per sessione browser; una nuova topologia sostituisce la precedente anche nelle altre schede. La chiave di sessione cambia a ogni avvio. Per uso multiutente in produzione servono una chiave persistente, un server WSGI e gestione degli esercizi per ID. Nessuna soluzione viene inclusa nello schema dei campi inviato al browser.

## Test

```powershell
python -m unittest discover -s tests -v
```

## Subnetting gerarchico

L’esercizio A usa `subnetting.py`: due firewall, tre router, otto LAN e tre aggregati. Le caselle sono posizionate sui CD e sotto i router; i transiti non sono assegnabili. Clic o trascinamento applicano una configurazione, Canc/Backspace svuota la casella. La verifica accetta assegnazioni alternative coerenti e controlla il più piccolo aggregato delle LAN scelte. Gli errori dettagliati sono disponibili nel suggerimento della casella. Riavviare Flask dopo modifiche Python e ricaricare la pagina.
