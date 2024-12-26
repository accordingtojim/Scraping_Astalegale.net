import sqlite3
import json
def import_json_to_sqlite(json_file, sqlite_db):
    # Carica il file JSON
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Connessione al database SQLite
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()

    # Creazione della tabella
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS aste (
        interessante TEXT,
        auction_id TEXT PRIMARY KEY,
        kpi_sconto FLOAT,
        Prezzo TEXT,
        "Valore di Stima" TEXT,
        "Offerta Minima" TEXT,        
        "Stato di Occupazione" TEXT,
        "Numero Aste Vuote" INTEGER,
        "Data Asta" TEXT,
        "Termine presentazione offerte" TEXT,
        "Modalità Gara" TEXT,
        Lotto TEXT,
        via TEXT, 
        comune TEXT,
        provincia TEXT,
        Indirizzo TEXT,
        Tipologia TEXT,
        Categoria TEXT,
        Storico_Aste TEXT,
        URL TEXT,
        Directory TEXT,
        "Valore di vendita giudiziaria" TEXT,
        "Conformità edilizia" TEXT,
        "Conformità catastale" TEXT,
        "Conformità urbanistica" TEXT,
        "Corrispondenza catasto" TEXT,
        "Superficie unità principali" TEXT,
        "Superficie unità accessorie" TEXT,
        "Valore stato di fatto" TEXT,
        "Valore netto decurtazioni" TEXT,
        "Valore stato di diritto" TEXT,
        "Spese annue" TEXT,
        "Spese annue deliberate" TEXT,
        "Spese annue scadute" TEXT,
        "Data valutazione" TEXT
    )
    ''')

    # Inserimento dei dati
    for record in data:
        storico_aste = json.dumps(record.get("Storico Aste", []))  # Converti lo storico in JSON string
        values = (
            record.get("interessante",None), record.get("auction_id"), record.get("kpi_sconto",None), record.get("via", None), record.get("comune", None), record.get("provincia", None),
            record.get("Indirizzo", None), record.get("Tipologia", None), record.get("Valore di Stima", None),
            record.get("Prezzo", None), record.get("Offerta Minima", None), record.get("Categoria", None),
            record.get("Stato di Occupazione", None), record.get("Data Asta", None), record.get("Lotto", None),
            record.get("Numero Aste Vuote", None), record.get("Termine presentazione offerte", None),
            record.get("Modalità Gara", None), storico_aste, record.get("URL", None), record.get("Directory", None),
            record.get("Valore di vendita giudiziaria", None), record.get("Conformità edilizia", None),
            record.get("Conformità catastale", None), record.get("Conformità urbanistica", None),
            record.get("Corrispondenza catasto", None), record.get("Superficie unità principali", None),
            record.get("Superficie unità accessorie", None), record.get("Valore stato di fatto", None),
            record.get("Valore netto decurtazioni", None), record.get("Valore stato di diritto", None),
            record.get("Spese annue", None), record.get("Spese annue deliberate", None),
            record.get("Spese annue scadute", None), record.get("Data valutazione", None)
        )

        cursor.execute('''
        INSERT OR REPLACE INTO aste (
            interessante, auction_id, kpi_sconto, via, comune, provincia, Indirizzo, Tipologia, "Valore di Stima",
            Prezzo, "Offerta Minima", Categoria, "Stato di Occupazione", "Data Asta", Lotto,
            "Numero Aste Vuote", "Termine presentazione offerte", "Modalità Gara", Storico_Aste,
            URL, Directory, "Valore di vendita giudiziaria", "Conformità edilizia", "Conformità catastale",
            "Conformità urbanistica", "Corrispondenza catasto", "Superficie unità principali",
            "Superficie unità accessorie", "Valore stato di fatto", "Valore netto decurtazioni",
            "Valore stato di diritto", "Spese annue", "Spese annue deliberate", "Spese annue scadute",
            "Data valutazione"
        ) VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', values)

    # Salva e chiudi
    conn.commit()
    conn.close()

    print(f"Dati importati nel database {sqlite_db} con successo!")








