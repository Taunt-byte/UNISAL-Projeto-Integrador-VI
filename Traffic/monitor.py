"""
Coleta em segundo plano:
  * uso de CPU, RAM e tráfego de rede (bytes enviados/recebidos por interface) via psutil
  * disponibilidade e latência dos servidores cadastrados (teste de conexão TCP)
"""
import socket
import threading
import time
from collections import deque
from datetime import datetime

import psutil

SAMPLE_SECONDS = 2        # intervalo entre amostras de CPU/RAM/rede
HISTORY_POINTS = 90       # 90 x 2 s = 3 minutos de gráfico
SERVER_CHECK_SECONDS = 30
SERVER_HISTORY = 20       # últimas verificações usadas para calcular a disponibilidade


def _now():
    return datetime.now().strftime("%H:%M:%S")


class SystemMonitor:
    def __init__(self):
        self.lock = threading.Lock()
        self.history = deque(maxlen=HISTORY_POINTS)
        self.interfaces = {}
        self.started_at = time.time()
        self.total_sent = 0
        self.total_recv = 0
        self._last = None
        self._last_time = None

    def sample(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        counters = psutil.net_io_counters(pernic=True)
        now = time.time()

        sent_rate = recv_rate = 0.0
        interfaces = {}
        if self._last is not None:
            dt = max(now - self._last_time, 0.001)
            for nic, c in counters.items():
                prev = self._last.get(nic)
                if prev is None:
                    continue
                s = max(c.bytes_sent - prev.bytes_sent, 0)
                r = max(c.bytes_recv - prev.bytes_recv, 0)
                sent_rate += s / dt
                recv_rate += r / dt
                self.total_sent += s
                self.total_recv += r
                interfaces[nic] = {
                    "sent_rate": s / dt, "recv_rate": r / dt,
                    "bytes_sent": c.bytes_sent, "bytes_recv": c.bytes_recv,
                    "errors": c.errin + c.errout, "drops": c.dropin + c.dropout,
                }
        self._last, self._last_time = counters, now

        point = {"t": _now(), "cpu": cpu, "ram": ram.percent,
                 "sent": sent_rate, "recv": recv_rate}
        with self.lock:
            if interfaces:
                self.interfaces = interfaces
            self.history.append(point)

    def snapshot(self):
        with self.lock:
            history = list(self.history)
            interfaces = dict(self.interfaces)
        elapsed = max(time.time() - self.started_at, 1)
        total = self.total_sent + self.total_recv
        freq = psutil.cpu_freq()
        ram = psutil.virtual_memory()
        try:
            connections = len(psutil.net_connections(kind="inet"))
        except (psutil.AccessDenied, PermissionError, OSError):
            connections = None  # no Windows/macOS pode exigir administrador
        return {
            "history": history,
            "current": history[-1] if history else None,
            "interfaces": interfaces,
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": int(freq.current) if freq else None,
            "ram_total": ram.total,
            "ram_used": ram.used,
            "connections": connections,
            "monitoring_seconds": int(elapsed),
            "total_sent": self.total_sent,
            "total_recv": self.total_recv,
            # projeção simples: se o consumo continuar nesse ritmo, quanto daria em 30 dias
            "monthly_projection": total / elapsed * 60 * 60 * 24 * 30,
        }

    def run(self):
        psutil.cpu_percent(interval=None)  # primeira leitura sempre retorna 0
        while True:
            try:
                self.sample()
            except Exception as e:  # nunca deixa a thread morrer
                print("Erro ao coletar métricas:", e)
            time.sleep(SAMPLE_SECONDS)


class ServerChecker:
    def __init__(self, db):
        self.db = db
        self.lock = threading.Lock()
        self.status = {}  # id -> dados da última verificação
        self._wake = threading.Event()

    @staticmethod
    def check(host, port, timeout=2.0):
        start = time.perf_counter()
        try:
            with socket.create_connection((host, int(port)), timeout=timeout):
                return True, round((time.perf_counter() - start) * 1000, 1), None
        except OSError as e:
            return False, None, str(e) or e.__class__.__name__

    def check_all(self):
        for srv in self.db.servers():
            online, latency, error = self.check(srv["host"], srv["port"])
            with self.lock:
                st = self.status.setdefault(srv["id"], {"history": deque(maxlen=SERVER_HISTORY)})
                st["history"].append({"t": _now(), "online": online, "latency": latency})
                st.update({"online": online, "latency": latency, "error": error, "checked_at": _now()})

    def snapshot(self):
        result = []
        with self.lock:
            for srv in self.db.servers():
                st = self.status.get(srv["id"])
                item = dict(srv)
                if st:
                    hist = list(st["history"])
                    item.update({
                        "online": st["online"], "latency": st["latency"], "error": st["error"],
                        "checked_at": st["checked_at"],
                        "uptime": round(100 * sum(h["online"] for h in hist) / len(hist), 1),
                        "history": hist,
                    })
                else:
                    item.update({"online": None, "latency": None, "error": None, "checked_at": None,
                                 "uptime": None, "history": []})
                result.append(item)
        return result

    def forget(self, server_id):
        with self.lock:
            self.status.pop(server_id, None)

    def check_now(self):
        self._wake.set()

    def run(self):
        while True:
            try:
                self.check_all()
            except Exception as e:
                print("Erro ao verificar servidores:", e)
            self._wake.wait(SERVER_CHECK_SECONDS)
            self._wake.clear()


def start_background(db):
    system = SystemMonitor()
    servers = ServerChecker(db)
    threading.Thread(target=system.run, daemon=True, name="system-monitor").start()
    threading.Thread(target=servers.run, daemon=True, name="server-checker").start()
    return system, servers
