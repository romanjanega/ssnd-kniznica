#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
from datetime import datetime
import re
from databaza import init_db, vloz_autora
from ol_diela import napln_diela

AUTORI = [
   # Stredovek
    "Dante Alighieri", "Geoffrey Chaucer", "François Villon",

    # Renesancia a humanizmus
    "William Shakespeare", "Miguel de Cervantes", "Giovanni Boccaccio",
    "Michel de Montaigne", "Christopher Marlowe",

    # Klasicizmus a osvietenstvo
    "Jean Racine", "Pierre Corneille",
    "Jean-Jacques Rousseau", "Jonathan Swift", "Daniel Defoe",
    "Alexander Pope", "Gotthold Ephraim Lessing",
    "Johann Wolfgang von Goethe", "Friedrich Schiller",

    # Romantizmus
    "George Gordon Byron", "Percy Bysshe Shelley", "John Keats",
    "Victor Hugo", "Alexandre Dumas", "Edgar Allan Poe", "Mary Shelley",
    "Walter Scott", "Mikhail Lermontov",

    # Realizmus a naturalizmus
    "Charles Dickens", "Honoré de Balzac",
    "Leo Tolstoy", "Fyodor Dostoevsky", "Ivan Turgenev",
    "Anton Pavlovič Čechov", "Mark Twain", "Henry James",

    # Modernizmus a 20. storočie
    "James Joyce", "Franz Kafka", "Virginia Woolf", "Marcel Proust",
    "Thomas Mann", "Rainer Maria Rilke", "Hermann Hesse",
    "D. H. Lawrence", "F. Scott Fitzgerald", "Ernest Hemingway",
    "William Faulkner", "George Orwell", "Aldous Huxley",
    "John Steinbeck", "Albert Camus", "Jean-Paul Sartre",
    "Antoine de Saint-Exupéry", "Samuel Beckett", "T. S. Eliot", "Ezra Pound",

    # 20.–21. storočie – svetová a populárna literatúra
    "Gabriel García Márquez", "Jorge Luis Borges", "Mario Vargas Llosa",
    "Paulo Coelho", "Chinua Achebe", "Haruki Murakami", "Kazuo Ishiguro",
    "Salman Rushdie", "Umberto Eco", "Milan Kundera", "Margaret Atwood",
    "Toni Morrison", "J. R. R. Tolkien", "C. S. Lewis", "J. K. Rowling",
    "Suzanne Collins", "George R. R. Martin", "Stephen King",
    "Agatha Christie", "Arthur Conan Doyle", "Ray Bradbury",
    "Isaac Asimov", "Philip K. Dick", "Joseph Conrad", "Jack London",
    "Oscar Wilde", "Emily Brontë", "Charlotte Brontë", "Jane Austen"
]

BASE = "https://openlibrary.org"

def split_meno_priezvisko(plne_meno):
    """Rozdelí meno a priezvisko (posledné slovo = priezvisko)."""
    meno = ""
    priezvisko = "Neznámy"
    if plne_meno:
        plne_meno = plne_meno.strip()
        casti = plne_meno.split()
        if len(casti) == 1:
            priezvisko = casti[0]
        else:
            meno = " ".join(casti[:-1])
            priezvisko = casti[-1]  
    return meno[:100], priezvisko[:50]


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
    # 1) presná fráza cez uvozovky
    query = f'"{meno}"'
    r = requests.get(f"{BASE}/search/authors.json",
                    params={"q": query, "limit": 10}, timeout=20)
    r.raise_for_status()
    docs = r.json().get("docs", [])
    if docs:
        docs.sort(key=lambda d: d.get("work_count", 0), reverse=True)
        return docs[0]
    return None


def detail_autora(author_key):
    """Načíta detaily autora podľa Open Library key."""
    url = f"{BASE}/authors/{author_key}.json"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    d = r.json()
    birth = parse_date(d.get("birth_date"))
    death = parse_date(d.get("death_date"))
    meno, priezvisko = split_meno_priezvisko(d.get("name"))
    return {
        "meno": meno,
        "priezvisko": priezvisko,
        "narodenie": birth,
        "umrtie": death,
        "ol_key": author_key[:10]
    }
     


# --- Hlavný program ---

def main():
    inserted = 0
    skipped = 0
    conn = init_db()
    for meno_autora in AUTORI:
        try:
            a = najdi_autora(meno_autora)
            if not a:
                print(f"❌ Nenašiel som: {meno_autora}")
                continue

            author_key = a.get("key", "").split("/")[-1]
            rec = detail_autora(author_key)
            id = vloz_autora(conn, rec)
            if id != -1:
                inserted += 1
                napln_diela(conn, id, rec["ol_key"])
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
