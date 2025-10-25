import sqlite3
import os

DB_PATH = "kniznica.db"
SQL_CREATE = "kniznica-create-table.sql"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    """Načíta SQL schému z externého súboru a vykoná ju."""
    if not os.path.exists(SQL_CREATE):
        print(f"❌ Súbor {SQL_CREATE} neexistuje!")
        exit(1)

    with open(SQL_CREATE, "r", encoding="utf-8") as f:
        sql_script = f.read()

    cur = conn.cursor()
    cur.executescript(sql_script)
    conn.commit()
    print(f"✅ Vytvorená SQL schéma zo súboru {SQL_CREATE}")
    return conn


def vloz_autora(conn, rec):
    """Vloží záznam do tabuľky autor."""
    # Získať nasledujúce ID
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM autor;")
    id = cur.fetchone()[0]
    # insert autor
    cur.execute("""
        INSERT OR IGNORE INTO autor (id, meno, priezvisko, narodenie, umrtie, ol_key)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (id, rec["meno"], rec["priezvisko"],
          rec["narodenie"], rec["umrtie"], rec["ol_key"]))
    conn.commit()
    result = -1
    if cur.rowcount == 1:
        result = id
    return result

def vloz_dielo(conn, autor_id, rec):
    """Vloží záznam do tabuľky dielo."""
    # Získať nasledujúce ID
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM dielo;")
    id = cur.fetchone()[0]
    # insert dielo
    cur.execute("""
        INSERT OR IGNORE INTO dielo (id, nazov, ol_key, autor_id)
        VALUES (?, ?, ?, ?);
    """, (id, rec["title"], rec["ol_key"], autor_id))
    conn.commit()
    return cur.rowcount
