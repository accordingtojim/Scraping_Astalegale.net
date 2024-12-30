import sqlite3
import json
from datetime import datetime

def import_json_to_sqlite(json_file, sqlite_db):
    # Carica il file JSON
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Connessione al database SQLite
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()

    # Creazione della tabella principale
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS aste (
        
        auction_id TEXT PRIMARY KEY,
        kpi_sconto FLOAT,
        via TEXT,
        comune TEXT,
        provincia TEXT,
        Indirizzo TEXT,
        Tipologia TEXT,
        "Valore di Stima" FLOAT,
        Prezzo FLOAT,
        "Offerta Minima" FLOAT,
        Categoria TEXT,
        "Stato di Occupazione" TEXT,
        "Data Asta" TEXT,
        Lotto INT,
        "Numero Aste Vuote" INTEGER,
        "Termine presentazione offerte" TEXT,
        "Modalità Gara" TEXT,
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
        "Data valutazione" TEXT,
        interessante TEXT,
        data_inserimento TEXT
    )
    ''')

    # Creazione della tabella storico
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS storico_aste (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auction_id TEXT,
        campo_modificato TEXT,
        valore_precedente TEXT,
        valore_nuovo TEXT,
        data_modifica TEXT
    )
    ''')

    # Inserimento o aggiornamento dei dati
    for record in data:
        auction_id = record.get("auction_id")
        data_inserimento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Controlla se l'asta esiste
        cursor.execute("SELECT * FROM aste WHERE auction_id = ?", (auction_id,))
        existing_record = cursor.fetchone()

        if existing_record:
            # Confronta i valori e registra le modifiche
            for idx, col in enumerate(cursor.description):
                col_name = col[0]
                existing_value = existing_record[idx]
                new_value = record.get(col_name, None)
                
                if col_name not in ("auction_id", "data_inserimento") and existing_value != new_value:
                    cursor.execute('''
                    INSERT INTO storico_aste (auction_id, campo_modificato, valore_precedente, valore_nuovo, data_modifica)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (auction_id, col_name, existing_value, new_value, data_inserimento))

            # Aggiorna la riga principale con i nuovi valori
            update_query = "UPDATE aste SET " + ", ".join([f'"{key}" = ?' for key in record.keys() if key != "auction_id" and key != "Storico Aste"]) + " WHERE auction_id = ?"
            update_values = [record.get(key, None) for key in record.keys() if key != "auction_id" and key != "Storico Aste"] + [auction_id]
            cursor.execute(update_query, update_values)
        else:
            # Inserisce un nuovo record
            insert_query = "INSERT INTO aste (" + ", ".join([f'"{key}"' for key in record.keys() if key != "Storico Aste"]) + ", data_inserimento) VALUES (" + ", ".join(["?" for key in record.keys() if key != "Storico Aste"]) + ", ?)"
            insert_values = [record.get(key, None) for key in record.keys() if key != "Storico Aste"] + [data_inserimento]
            cursor.execute(insert_query, insert_values)

    # Salva e chiudi
    conn.commit()
    conn.close()

    print(f"Dati importati e aggiornati nel database {sqlite_db} con successo!")


