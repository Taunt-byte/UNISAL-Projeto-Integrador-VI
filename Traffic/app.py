"""
NetMonitor - Projeto Integrador VI (UNISAL)

Sistema web de monitoramento de redes corporativas:
  * tráfego de rede em tempo real (upload/download por interface) e projeção de consumo
  * uso de CPU e memória do servidor
  * disponibilidade e latência de servidores/serviços cadastrados
  * registro dos dispositivos que acessam o sistema (IP, localização, SO, navegador)

Como rodar (dentro da pasta Traffic):
    pip install -r requirements.txt
    python app.py            -> só neste computador  (http://127.0.0.1:5000)
    python app.py --rede     -> outros dispositivos da rede também podem acessar
"""
import argparse
import hashlib
import ipaddress
import json
import os
import random
import threading
import urllib.request
from datetime import datetime, timedelta

from flask import (Flask, render_template, request, session, jsonify, g,
                   send_from_directory, abort)

from dbsetup import Database
import monitor

try:
    import httpagentparser
except ImportError:
    httpagentparser = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(os.path.dirname(BASE_DIR), "img")

app = Flask(__name__)
app.json.sort_keys = False  # mantém a ordem dos gráficos (mais acessados primeiro)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

db = Database()

# Limites que geram alertas no painel
ALERT_CPU = 85
ALERT_RAM = 90
ALERT_LATENCY_MS = 300

IGNORED_PREFIXES = ("/static", "/img", "/api", "/favicon.ico")
_geo_cache = {}

# As threads de monitoramento só começam no processo que atende as requisições
_bg_lock = threading.Lock()
_bg = {}


def background():
    with _bg_lock:
        if not _bg:
            _bg["system"], _bg["servers"] = monitor.start_background(db)
    return _bg["system"], _bg["servers"]


# ---------------------------------------------------------------------------
# Registro de visitantes
# ---------------------------------------------------------------------------
def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "0.0.0.0"


def parse_user_agent(ua):
    ua = ua or ""
    if httpagentparser:
        info = httpagentparser.detect(ua)
        os_name = (info.get("platform") or info.get("os") or {}).get("name")
        browser = (info.get("browser") or {}).get("name")
        if os_name or browser:
            return os_name or "Desconhecido", browser or "Desconhecido"
    os_name = next((n for k, n in [("Windows", "Windows"), ("Android", "Android"), ("iPhone", "iOS"),
                                   ("iPad", "iOS"), ("Mac OS", "macOS"), ("Linux", "Linux")] if k in ua),
                   "Desconhecido")
    browser = next((n for k, n in [("Edg/", "Edge"), ("OPR/", "Opera"), ("Chrome/", "Chrome"),
                                   ("Firefox/", "Firefox"), ("Safari/", "Safari")] if k in ua),
                   "Desconhecido")
    return os_name, browser


def geolocate(ip):
    """Retorna (continente, país, cidade). Nunca lança erro."""
    try:
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return "Rede local", "Rede local", "Rede local"
    except ValueError:
        return "Desconhecido", "Desconhecido", "Desconhecido"
    if ip in _geo_cache:
        return _geo_cache[ip]
    result = ("Desconhecido", "Desconhecido", "Desconhecido")
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,continent,country,city&lang=pt-BR"
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") == "success":
            result = (data.get("continent") or "Desconhecido",
                      data.get("country") or "Desconhecido",
                      data.get("city") or "Desconhecido")
    except Exception as e:
        print("Não foi possível localizar o IP", ip, "-", e)
    _geo_cache[ip] = result
    return result


@app.before_request
def track_visitor():
    background()
    if request.path.startswith(IGNORED_PREFIXES):
        return
    sid = session.get("user")
    if sid and db.session_exists(sid):
        g.session_id = sid
        return
    ip = get_client_ip()
    now = datetime.now().replace(microsecond=0)
    sid = hashlib.md5((str(now) + ip + os.urandom(4).hex()).encode("utf-8")).hexdigest()
    session["user"] = sid
    g.session_id = sid
    os_name, browser = parse_user_agent(request.headers.get("User-Agent"))
    db.create_session([ip, *geolocate(ip), os_name, browser, sid, str(now)])


@app.after_request
def register_page(response):
    page = PAGE_NAMES.get(request.endpoint)
    if page and response.status_code == 200 and getattr(g, "session_id", None):
        db.register_page(page, g.session_id, str(datetime.now().replace(microsecond=0)))
    return response


PAGE_NAMES = {"overview": "Visão geral", "network": "Rede", "servers_page": "Servidores",
              "visitors": "Visitantes", "about": "Sobre"}


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------
@app.route("/")
def overview():
    return render_template("index.html", active="overview")


@app.route("/rede")
def network():
    return render_template("rede.html", active="network")


@app.route("/servidores")
def servers_page():
    return render_template("servidores.html", active="servers")


@app.route("/dashboard")
def visitors():
    return render_template("dashboard.html", active="visitors")


@app.route("/about")
def about():
    return render_template("about.html", active="about")


@app.route("/minha-sessao")
def my_session():
    return session_pages(g.session_id)


@app.route("/dashboard/<session_id>")
def session_pages(session_id):
    info = db.session_info(session_id)
    if info is None:
        abort(404)
    return render_template("dashboard-single.html", data=db.user_visits(session_id), info=info,
                           mine=(session_id == g.get("session_id")), active="visitors")


@app.route("/img/<path:filename>")
def images(filename):
    return send_from_directory(IMG_DIR, filename)


# ---------------------------------------------------------------------------
# API (JSON) usada pelos gráficos
# ---------------------------------------------------------------------------
@app.route("/api/system")
def api_system():
    system, _ = background()
    return jsonify(system.snapshot())


@app.route("/api/servers", methods=["GET"])
def api_servers():
    _, servers = background()
    return jsonify(servers.snapshot())


@app.route("/api/servers", methods=["POST"])
def api_add_server():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    host = (data.get("host") or "").strip()
    try:
        port = int(data.get("port"))
    except (TypeError, ValueError):
        port = 0
    if not name or not host or not (1 <= port <= 65535):
        return jsonify({"error": "Informe nome, endereço e uma porta entre 1 e 65535."}), 400
    new_id = db.add_server(name[:80], host[:200], port)
    background()[1].check_now()
    return jsonify({"id": new_id}), 201


@app.route("/api/servers/<int:server_id>", methods=["DELETE"])
def api_delete_server(server_id):
    db.delete_server(server_id)
    background()[1].forget(server_id)
    return "", 204


@app.route("/api/servers/check", methods=["POST"])
def api_check_servers():
    background()[1].check_now()
    return "", 202


@app.route("/api/sessions")
def api_sessions():
    keys = ["ip", "continent", "country", "city", "os", "browser", "session", "demo"]
    return jsonify([{**{k: r[k] for k in keys}, "time": r["created_at"]} for r in db.sessions()])


@app.route("/api/stats")
def api_stats():
    return jsonify(db.stats())


@app.route("/api/charts")
def api_charts():
    return jsonify(db.charts())


@app.route("/api/alerts")
def api_alerts():
    system, servers = background()
    alerts = []
    cur = system.snapshot()["current"]
    if cur:
        if cur["cpu"] >= ALERT_CPU:
            alerts.append({"level": "danger", "text": f"CPU em {cur['cpu']:.0f}% (limite {ALERT_CPU}%)"})
        if cur["ram"] >= ALERT_RAM:
            alerts.append({"level": "danger", "text": f"Memória em {cur['ram']:.0f}% (limite {ALERT_RAM}%)"})
    for s in servers.snapshot():
        if s["online"] is False:
            alerts.append({"level": "danger", "text": f"{s['name']} ({s['host']}:{s['port']}) está fora do ar"})
        elif s["latency"] and s["latency"] >= ALERT_LATENCY_MS:
            alerts.append({"level": "warning", "text": f"{s['name']} com latência alta: {s['latency']} ms"})
    return jsonify(alerts)


# ---------------------------------------------------------------------------
# Modo demonstração: gera visitantes fictícios para o painel não ficar vazio
# ---------------------------------------------------------------------------
DEMO_PLACES = [
    ("América do Sul", "Brasil", "São Paulo"), ("América do Sul", "Brasil", "Campinas"),
    ("América do Sul", "Brasil", "Americana"), ("América do Sul", "Brasil", "Rio de Janeiro"),
    ("América do Sul", "Brasil", "Belo Horizonte"), ("América do Sul", "Argentina", "Buenos Aires"),
    ("América do Norte", "Estados Unidos", "Nova York"), ("Europa", "Portugal", "Lisboa"),
    ("Europa", "Alemanha", "Berlim"), ("Rede local", "Rede local", "Rede local"),
]
DEMO_DEVICES = [("Windows", "Chrome"), ("Windows", "Edge"), ("Windows", "Firefox"), ("Android", "Chrome"),
                ("iOS", "Safari"), ("macOS", "Safari"), ("Linux", "Firefox"), ("Android", "Samsung Internet")]


@app.route("/api/demo", methods=["POST"])
def api_demo():
    n = min(int((request.get_json(silent=True) or {}).get("n", 25)), 200)
    now = datetime.now().replace(microsecond=0)
    sessions, pages = [], []
    for _ in range(n):
        when = now - timedelta(minutes=random.randint(0, 24 * 60))
        place = random.choices(DEMO_PLACES, weights=[30, 15, 10, 10, 8, 4, 4, 3, 2, 14])[0]
        os_name, browser = random.choices(DEMO_DEVICES, weights=[30, 10, 6, 25, 12, 6, 4, 7])[0]
        ip = "192.168.0.%d" % random.randint(2, 254) if place[0] == "Rede local" else \
             random.choice(["203.0.113.%d", "198.51.100.%d"]) % random.randint(1, 254)  # faixas de exemplo (RFC 5737)
        sid = hashlib.md5(os.urandom(16)).hexdigest()
        sessions.append((ip, *place, os_name, browser, sid, str(when), 1))
        for page in random.sample(list(PAGE_NAMES.values()), random.randint(1, 4)):
            pages.append((page, sid, str(when), random.randint(1, 6)))
    db.run_many("""INSERT INTO sessions(ip, continent, country, city, os, browser, session, created_at, demo)
                   VALUES (?,?,?,?,?,?,?,?,?)""", sessions)
    db.run_many("INSERT INTO pages(name, session, first_visited, visits) VALUES (?,?,?,?)", pages)
    return jsonify({"created": n}), 201


@app.route("/api/demo", methods=["DELETE"])
def api_clear_demo():
    db.clear_demo()
    return "", 204


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NetMonitor - Projeto Integrador VI")
    parser.add_argument("--rede", action="store_true", help="permite acesso de outros dispositivos da rede")
    parser.add_argument("--porta", type=int, default=5000)
    args = parser.parse_args()
    host = "0.0.0.0" if args.rede else "127.0.0.1"
    print(f"\n  NetMonitor rodando em http://127.0.0.1:{args.porta}")
    if args.rede:
        print("  Outros dispositivos: http://<IP deste computador>:%d\n" % args.porta)
    app.run(host=host, port=args.porta, debug=False, threaded=True)
