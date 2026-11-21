"""Camada de banco de dados (SQLite) do monitor de tráfego."""
import os
import sqlite3
import threading

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pythonsqlite.db")

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS pages (
        id integer PRIMARY KEY,
        name varchar(225) NOT NULL,
        session varchar(255) NOT NULL,
        first_visited datetime NOT NULL,
        visits integer NOT NULL Default 1
    );""",
    """CREATE TABLE IF NOT EXISTS sessions (
        id integer PRIMARY KEY,
        ip varchar(225) NOT NULL,
        continent varchar(225) NOT NULL,
        country varchar(225) NOT NULL,
        city varchar(225) NOT NULL,
        os varchar(225) NOT NULL,
        browser varchar(225) NOT NULL,
        session varchar(225) NOT NULL,
        created_at datetime NOT NULL,
        demo integer NOT NULL DEFAULT 0
    );""",
    """CREATE TABLE IF NOT EXISTS servers (
        id integer PRIMARY KEY,
        name varchar(225) NOT NULL,
        host varchar(225) NOT NULL,
        port integer NOT NULL
    );""",
]

DEFAULT_SERVERS = [
    ("Google", "google.com", 443),
    ("GitHub", "github.com", 443),
    ("Cloudflare DNS", "1.1.1.1", 53),
    ("Google DNS", "8.8.8.8", 53),
]


class Database:
    """Conexão única compartilhada entre as threads, protegida por um lock."""

    def __init__(self, path=DATABASE):
        self.path = path
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self.conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        self._init()

    def _init(self):
        with self.lock:
            for sql in SCHEMA:
                self.conn.execute(sql)
            # Migração: bancos antigos (versão 2021) não têm a coluna "demo"
            cols = [r["name"] for r in self.conn.execute("PRAGMA table_info(sessions)").fetchall()]
            if "demo" not in cols:
                self.conn.execute("ALTER TABLE sessions ADD COLUMN demo integer NOT NULL DEFAULT 0")
            if self.conn.execute("SELECT COUNT(*) AS n FROM servers").fetchone()["n"] == 0:
                self.conn.executemany("INSERT INTO servers(name, host, port) VALUES (?,?,?)", DEFAULT_SERVERS)

    def all(self, sql, params=()):
        with self.lock:
            return self.conn.execute(sql, params).fetchall()

    def one(self, sql, params=()):
        with self.lock:
            return self.conn.execute(sql, params).fetchone()

    def run(self, sql, params=()):
        with self.lock:
            return self.conn.execute(sql, params).lastrowid

    def run_many(self, sql, rows):
        with self.lock:
            self.conn.execute("BEGIN")
            self.conn.executemany(sql, rows)
            self.conn.execute("COMMIT")

    # ----------------------------------------------------------- sessões/páginas
    def session_exists(self, session_id):
        return self.one("SELECT 1 AS ok FROM sessions WHERE session = ?", [session_id]) is not None

    def create_session(self, data, demo=0):
        self.run("""INSERT INTO sessions(ip, continent, country, city, os, browser, session, created_at, demo)
                    VALUES (?,?,?,?,?,?,?,?,?)""", list(data) + [demo])

    def register_page(self, name, session_id, when):
        row = self.one("SELECT id FROM pages WHERE name=? AND session=?", [name, session_id])
        if row is None:
            self.run("INSERT INTO pages(name, session, first_visited) VALUES (?,?,?)", [name, session_id, when])
        else:
            self.run("UPDATE pages SET visits = visits + 1 WHERE id = ?", [row["id"]])

    def sessions(self):
        return self.all("SELECT * FROM sessions ORDER BY created_at DESC")

    def user_visits(self, session_id):
        return self.all("SELECT * FROM pages WHERE session = ? ORDER BY first_visited", [session_id])

    def session_info(self, session_id):
        return self.one("SELECT * FROM sessions WHERE session = ?", [session_id])

    def stats(self):
        return {
            "total_sessions": self.one("SELECT COUNT(*) AS n FROM sessions")["n"],
            "total_visitors": self.one("SELECT COUNT(DISTINCT ip) AS n FROM sessions")["n"],
            "total_pageviews": self.one("SELECT COALESCE(SUM(visits),0) AS n FROM pages")["n"],
            "unique_pageviews": self.one("SELECT COUNT(*) AS n FROM pages")["n"],
            "demo_sessions": self.one("SELECT COUNT(*) AS n FROM sessions WHERE demo = 1")["n"],
        }

    def charts(self):
        def group(sql):
            return {r["k"]: r["n"] for r in self.all(sql)}
        return {
            "pages": group("SELECT name AS k, SUM(visits) AS n FROM pages GROUP BY name ORDER BY n DESC"),
            "os": group("SELECT os AS k, COUNT(*) AS n FROM sessions GROUP BY os ORDER BY n DESC"),
            "browser": group("SELECT browser AS k, COUNT(*) AS n FROM sessions GROUP BY browser ORDER BY n DESC"),
            "country": group("SELECT country AS k, COUNT(*) AS n FROM sessions GROUP BY country ORDER BY n DESC LIMIT 8"),
            "by_hour": group("SELECT substr(created_at, 12, 2) AS k, COUNT(*) AS n FROM sessions GROUP BY k ORDER BY k"),
        }

    def clear_demo(self):
        with self.lock:
            self.conn.execute("BEGIN")
            self.conn.execute("DELETE FROM pages WHERE session IN (SELECT session FROM sessions WHERE demo = 1)")
            self.conn.execute("DELETE FROM sessions WHERE demo = 1")
            self.conn.execute("COMMIT")

    # ----------------------------------------------------------------- servidores
    def servers(self):
        return self.all("SELECT * FROM servers ORDER BY id")

    def add_server(self, name, host, port):
        return self.run("INSERT INTO servers(name, host, port) VALUES (?,?,?)", [name, host, port])

    def delete_server(self, server_id):
        self.run("DELETE FROM servers WHERE id = ?", [server_id])


if __name__ == "__main__":
    Database()
    print("Banco pronto em:", DATABASE)
