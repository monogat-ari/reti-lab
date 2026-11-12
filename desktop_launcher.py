"""Standalone Windows launcher. All services are bound to loopback only."""
import ctypes
import json
import sys
import threading
import http.client
import webbrowser
from pathlib import Path

def main():
    server = None
    thread = None
    report = None
    try:
        from app import app
        from werkzeug.serving import make_server
        # OS-assigned port: never stop or hijack another local application.
        server = make_server('127.0.0.1', 0, app, threaded=True)
        url = f'http://127.0.0.1:{server.server_port}/'
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        cookie = ''
        def fetch(path, data=None):
            nonlocal cookie
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
            try:
                headers = {'Content-Type':'application/json', 'Cookie':cookie}
                conn.request('POST' if data is not None else 'GET', '/'+path,
                             json.dumps(data) if data is not None else None, headers)
                response = conn.getresponse()
                if response.getheader('Set-Cookie'):
                    cookie = response.getheader('Set-Cookie').split(';',1)[0]
                body = response.read()
                if response.status != 200: raise RuntimeError(f'HTTP {response.status}: {path}')
                return body
            finally:
                conn.close()
        fetch('')
        if '--self-test' in sys.argv:
            report = Path(sys.argv[sys.argv.index('--self-test') + 1])
            checks = {}
            for asset in ['static/app.js', 'static/style.css']:
                checks[asset] = len(fetch(asset)) > 100
            for mode in ['A', 'B']:
                exercise = json.loads(fetch('api/new', {'mode':mode}))
                checks[mode] = bool(exercise['nodes']) and bool(exercise['edges'])
                result = json.loads(fetch('api/check', {}))
                checks[mode+' check'] = result['score'] == 0 and result['total'] > 0
            if not all(checks.values()):
                raise RuntimeError(str(checks))
            report.write_text(json.dumps({'ok':True,'checks':checks}), encoding='utf-8')
        else:
            webbrowser.open(url)
            # A native control window requires no external GUI framework.
            ctypes.windll.user32.MessageBoxW(
                None,
                'Reti Lab e avviato nel browser.\n\n'
                'Lascia aperta questa finestra mentre svolgi gli esercizi.\n'
                'Puoi ridurre le altre finestre e usare normalmente il browser.\n\n'
                f'Indirizzo: {url}\n\n'
                'Premi OK per ARRESTARE Reti Lab.\n'
                'Per riaprirlo, fai doppio clic sull\'eseguibile.',
                'Reti Lab - programma in esecuzione', 0x40)
    except Exception as exc:
        if '--self-test' in sys.argv:
            report = Path(sys.argv[sys.argv.index('--self-test') + 1])
            report.write_text(json.dumps({'ok':False,'error':str(exc),'traceback':__import__('traceback').format_exc()}), encoding='utf-8')
        else:
            ctypes.windll.user32.MessageBoxW(None, str(exc), 'Reti Lab - errore di avvio', 0x10)
        return 1
    finally:
        if server is not None:
            if thread is not None:
                server.shutdown()
                thread.join(timeout=5)
            server.server_close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

