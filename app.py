import secrets
from flask import Flask, request, jsonify, render_template, session
from models import generate
from subnetting import generate_subnetting, check_subnetting

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=65536, SESSION_COOKIE_SAMESITE='Lax')

@app.get('/')
def index(): return render_template('index.html')

@app.post('/api/new')
def new():
    mode = (request.get_json(silent=True) or {}).get('mode','A')
    if mode not in ['A','B']: return jsonify(error='ModalitÃ  non valida'),400
    session['seed'] = secrets.randbits(32); session['mode'] = mode
    if mode == 'A':
        for attempt in range(100):
            public, _ = generate_subnetting(session['seed'])
            if public['shape'] != session.get('last_shape'): break
            session['seed'] = secrets.randbits(32)
        session['last_shape'] = public['shape']
        return jsonify(public)
    return jsonify(generate(session['seed']).public(mode))

@app.post('/api/check')
def check():
    if 'seed' not in session: return jsonify(error='Genera un esercizio'),400
    data = request.get_json(silent=True) or {}
    if not isinstance(data,dict): return jsonify(error='Risposte non valide'),400
    results = {}
    if session['mode'] == 'A':
        public, solutions = generate_subnetting(session['seed'])
        results = check_subnetting(public, solutions, data)
        return jsonify(results=results, score=sum(r['correct'] for r in results.values()), total=len(results))
    else:
        t = generate(session['seed'])
        for r in t.rows:
            values = data.get(r['id'],[])
            if not isinstance(values,list): values=[]
            checks = [i < len(values) and str(values[i]).strip() == f['answer'] for i,f in enumerate(r['fields'])]
            results[r['id']] = dict(correct=all(checks) and len(values)==len(checks),fields=checks,message='Controlla i campi evidenziati; rispetta lâ€™ordine richiesto.')
    return jsonify(results=results, score=sum(r['correct'] for r in results.values()), total=len(results))

if __name__ == '__main__': app.run(host='127.0.0.1',port=5000)
