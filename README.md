# Reti Lab

Piattaforma didattica per esercitarsi con le reti di calcolatori, con generazione di topologie e correzione automatica degli esercizi di subnetting IPv4, routing e firewall.

## Avvio su Windows

1. [Scarica RetiLab.exe](https://github.com/monogat-ari/reti-lab/raw/refs/heads/main/RetiLab.exe) e fai doppio clic sul file scaricato.
2. Il programma apre automaticamente il browser predefinito. Lascia aperta la finestra «Reti Lab - programma in esecuzione» mentre svolgi gli esercizi.
3. Per fermare il programma, premi **OK** nella finestra di Reti Lab.

L’eseguibile è per Windows a 64 bit, include Python e Flask e funziona offline. Il server si avvia sul solo indirizzo locale `127.0.0.1` e sceglie una porta libera a ogni avvio.

Il file è privo di firma digitale. Microsoft Defender SmartScreen può mostrare un avviso al primo avvio e i criteri di sicurezza dei PC gestiti possono bloccarlo. Su un PC gestito, rivolgiti all’amministratore.

## Avvio dai sorgenti

Servono Python 3.10 o successivo e le dipendenze elencate in `requirements.txt`. Da PowerShell, nella cartella del progetto, esegui questi comandi.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Apri [http://127.0.0.1:5000](http://127.0.0.1:5000) nel browser. Su Windows puoi usare `py` al posto di `python` per creare l’ambiente virtuale.

## Modello

`models.py` contiene Subnet, Node, Topology e generate(seed). La topologia connessa varia numero delle LAN, requisiti host e indirizzi; lo scheletro Internet–F1–router DMZ/RED resta fisso per produrre esercizi coerenti. Il gateway è il primo host, il PC rappresentativo il secondo. minIP include il gateway. I transiti sono /30 e non vengono assegnati nell’esercizio A. Le allocazioni LAN sono allineate e disgiunte. Le opzioni possono essere assegnate a qualunque CD compatibile: il backend verifica capacità minima, broadcast e assenza di sovrapposizioni, senza imporre un’unica permutazione.

Il formulario B è generato da uno schema backend: solo indirizzi, subnet, porte e interfacce sono input testuali. La correzione è per campo e richiede l’ordine proposto, non è un interprete di tutte le sintassi iptables equivalenti. Gli esercizi sulle rotte statiche usano la sintassi `route add ... gw ... dev ...`. Le regole sono esercizi mirati, non una configurazione completa pronta per una rete reale. Si assumono forwarding e rotte di ritorno già configurati. Internet è simulato tramite indirizzi TEST-NET e TAP.

Lo stato è per sessione browser; una nuova topologia sostituisce la precedente anche nelle altre schede. La chiave di sessione cambia a ogni avvio. Per uso multiutente in produzione servono una chiave persistente, un server WSGI e gestione degli esercizi per ID. Nessuna soluzione viene inclusa nello schema dei campi inviato al browser.

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Subnetting gerarchico

L’esercizio A usa `subnetting.py`: due firewall, tre router, otto LAN e tre aggregati. I valori `minIP` sono distinti e richiedono sei prefissi, da `/27` a `/22`. Le caselle sono posizionate sui CD e sotto i router; i transiti non sono assegnabili. Clic o trascinamento applicano una configurazione, Canc/Backspace svuota la casella. La verifica accetta assegnazioni alternative coerenti e controlla il più piccolo aggregato delle LAN scelte. Gli errori dettagliati sono disponibili nel suggerimento della casella. Riavviare Flask dopo modifiche Python e ricaricare la pagina.
