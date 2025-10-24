#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import requests
import time
from datetime import datetime
import re
import os


DB_PATH = "kniznica.db"
SQL_CREATE = "kniznica-create-table.sql"

#from autori import AUTORI
AUTORI = [
    "Fyodor Dostoevsky", "Mark Twain", "George Orwell", "Franz Kafka",
    "Ernest Hemingway", "F. Scott Fitzgerald", "Albert Camus", "Gabriel García Márquez",
    "J. R. R. Tolkien", "Agatha Christie", "Oscar Wilde", "Dante Alighieri"
]

BASE = "https://openlibrary.org"


# --- Pomocné funkcie ---

def split_meno_priezvisko(plne_meno):
    """Rozdelí meno a priezvisko (posledné slovo = priezvisko)."""
    if not plne_meno:
        return "", "Neznámy"
    plne_meno = plne_meno.strip()
    casti = plne_meno.split()
    if len(casti) == 1:
        return "", casti[0]
    priezvisko = casti[-1]
    return plne_meno[:100], priezvisko[:50]


def parse_date(d):
    """Pokúsi sa previesť rôzne formáty dátumu na ISO tvar YYYY-MM-DD.
       Ak sa nepodarí, vráti None."""
    if not d:
        return None

    d = d.strip()
    # 1) Ak je už v tvare YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        return d
    # 2) Rôzne bežné formáty, ktoré sa objavujú v Open Library
    vzory = [
        "%d %B %Y",      # 16 October 1854
        "%B %d %Y",      # October 16 1854
        "%B %d, %Y",     # October 16, 1854
        "%d %b %Y",      # 16 Oct 1854
        "%b %d %Y",      # Oct 16 1854
        "%Y.%m.%d",      # 1854.10.16
        "%d.%m.%Y",      # 16.10.1854
        "%Y/%m/%d",      # 1854/10/16
    ]

    for vzor in vzory:
        try:
            dt = datetime.strptime(d, vzor)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # 3) Ak obsahuje len rok (napr. "1854")
    m = re.search(r"(\d{4})", d)
    if m:
        return f"{m.group(1)}-01-01"

    # 4) Inak neznámy formát
    return None


def najdi_autora(meno):
    """Vyhľadá autora podľa mena."""
    url = f"{BASE}/search/authors.json"
    r = requests.get(url, params={"q": meno, "limit": 1}, timeout=20)
    r.raise_for_status()
    data = r.json()
    docs = data.get("docs", [])
    return docs[0] if docs else None


def detail_autora(author_key):
    """Načíta detaily autora podľa Open Library key."""
    url = f"{BASE}/authors/{author_key}.json"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def run_sql(conn,file_path):
    """Načíta SQL schému z externého súboru a vykoná ju."""
    if not os.path.exists(file_path):
        print(f"❌ Súbor {file_path} neexistuje!")
        exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        sql_script = f.read()

    cur = conn.cursor()
    cur.executescript(sql_script)
    conn.commit()

def dalsie_id(conn):
    """Zistí nasledujúce voľné ID."""
    c = conn.cursor()
    c.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM autor;")
    return c.fetchone()[0]


def vloz_autora(conn, rec):
    """Vloží záznam do tabuľky autor."""
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO autor (id, meno, priezvisko, narodenie, umrtie, ol_key)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (rec["id"], rec["meno"], rec["priezvisko"],
          rec["narodenie"], rec["umrtie"], rec["ol_key"]))
    conn.commit()
    return cur.rowcount


# --- Hlavný program ---

def main():
    conn = sqlite3.connect(DB_PATH)
    run_sql(conn, SQL_CREATE)
    print(f"✅ Vytvorená SQL schéma zo súboru {SQL_CREATE}")


    inserted = 0
    skipped = 0

    for meno_autora in AUTORI:
        try:
            a = najdi_autora(meno_autora)
            if not a:
                print(f"❌ Nenašiel som: {meno_autora}")
                continue

            author_key = a.get("key", "").split("/")[-1]
            d = detail_autora(author_key)

            birth = parse_date(d.get("birth_date"))
            death = parse_date(d.get("death_date"))
            meno, priezvisko = split_meno_priezvisko(d.get("name") or a.get("name"))

            rec = {
                "id": dalsie_id(conn),
                "meno": meno,
                "priezvisko": priezvisko,
                "narodenie": birth,
                "umrtie": death,
                "ol_key": author_key[:10]
            }

            rows = vloz_autora(conn, rec)
            if rows == 1:
                inserted += 1
                print(f"✅ {rec['meno']} {rec['priezvisko']} ({rec['ol_key']})")
            else:
                skipped += 1
                print(f"↩️ Preskočené (duplicitný ol_key): {meno_autora}")

            time.sleep(0.2)

        except Exception as e:
            print(f"⚠️ Chyba pri '{meno_autora}': {e}")

    print(f"\nHotovo. Vložené: {inserted}, preskočené: {skipped}")
    conn.close()


if __name__ == "__main__":
    main()
