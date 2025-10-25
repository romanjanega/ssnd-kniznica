import requests
from databaza import vloz_dielo

BASE = "https://openlibrary.org"

def ziskaj_diela_autora(ol_key, limit=50):
    """Získa zoznam diel pre daného autora z OpenLibrary."""
    url = f"{BASE}/authors/{ol_key}/works.json"
    try:
        r = requests.get(url, params={"limit": limit}, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("entries", [])
    except Exception as e:
        print(f"⚠️ Chyba pri získavaní diel autora {ol_key}: {e}")
        return []

def ziskaj_dielo(ol_key):
    """Získa detail diela podľa jeho Open Library key."""
    url = f"{BASE}/works/{ol_key}.json"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"⚠️ Chyba pri získavaní diela {ol_key}: {e}")
        return None

def napln_diela(conn, autor_id, ol_key):
    """Načíta a vloží diela autora do databázy."""
    diela = ziskaj_diela_autora(ol_key, limit=100)
    inserted = 0
    for dielo in diela:
        title = dielo.get("title")
        if title is None or title.strip() == "":
            # preskoc dielo bez nazvu
            continue
        # detail diela
        detail = ziskaj_dielo(dielo.get("key", "").split("/")[-1])
        autori = detail.get("authors", []) if detail else []
        if( not autori or len(autori) > 1):
            # preskoc viacautorove diela
            continue
        rec = {
            "title": title[:200],
            "ol_key": dielo.get("key", "").split("/")[-1]
        }
        rows = vloz_dielo(conn, autor_id, rec)
        if rows == 1:
            inserted += 1
            print(f"   ✅ Vložené dielo: {rec['title']} ({rec['ol_key']})")
        else:
            print(f"   ↩️ Preskočené dielo (duplicitný ol_key): {rec['title']}")
    return inserted