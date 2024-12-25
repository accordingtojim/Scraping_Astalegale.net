import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
import re
import os
import json

def preprocess_image(image):
    """
    Migliora la qualità delle immagini per l'OCR.
    """
    # Converti l'immagine in scala di grigi
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    # Applica una soglia binaria per migliorare il contrasto
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Rimuove il rumore
    processed_image = cv2.medianBlur(binary, 3)
    return Image.fromarray(processed_image)

def extract_text_from_pdf(pdf_path, numero_lotto):
    """
    Estrae il testo da un PDF, combinando OCR per immagini e testo nativo.
    Se numero_lotto != 1, estrae il testo successivo alla prima occorrenza della stringa "LOTTO {numero_lotto}".
    """
    text = ""
    try:
        # Prova a leggere il testo nativo
        pdf_document = fitz.open(pdf_path)
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)

            # Prova a estrarre il testo nativo
            page_text = page.get_text()
            if page_text.strip():
                # Filtra le righe indesiderate
                filtered_lines = [
                    line for line in page_text.splitlines()
                    if "pagina" not in line.strip().lower() 
                    and "astalegale.net" not in line.strip().lower()
                ]
                text += "\n".join(filtered_lines)
            else:
                # Se non c'è testo nativo, estrai l'immagine e usa OCR
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes("png")))

                # Inizializza `processed_img` per evitare errori
                processed_img = img

                # OCR senza pre-elaborazione
                page_text = pytesseract.image_to_string(img, lang="ita")

                # Se l'OCR fallisce, prova con la pre-elaborazione
                if not page_text.strip():
                    try:
                        processed_img = preprocess_image(img)
                        page_text = pytesseract.image_to_string(processed_img, lang="ita")
                    except Exception as e:
                        print(f"Errore durante la pre-elaborazione o OCR: {e}")
                        page_text = ""  # Nel caso fallisca anche la pre-elaborazione

                # Filtra le righe indesiderate
                filtered_lines = [
                    line for line in page_text.splitlines()
                    if "pagina" not in line.strip().lower() 
                    and "astalegale.net" not in line.strip().lower()
                ]
                text += "\n".join(filtered_lines) + "\n"

        pdf_document.close()

        # Se numero_lotto != 1, estrai solo il testo successivo alla stringa "LOTTO {numero_lotto}"
        if numero_lotto != 1:
            lotto_string = f"LOTTO {numero_lotto}".lower()
            text_lines = text.splitlines()

            # Trova la prima occorrenza della stringa "LOTTO {numero_lotto}"
            try:
                start_index = next(i for i, line in enumerate(text_lines) if lotto_string in line.lower())
                text = "\n".join(text_lines[start_index + 1:])
            except StopIteration:
                # Se la stringa non viene trovata, restituisci un testo vuoto o un messaggio di errore
                text = ""  # Oppure "Stringa 'LOTTO {numero_lotto}' non trovata."

    except Exception as e:
        print(f"Errore durante l'elaborazione del PDF {pdf_path}: {e}")
    
    return text

def extract_text_between_titles(text, start_title, end_title):
    """
    Estrae il testo tra due titoli specificati.

    Args:
        text (str): Il testo completo in cui cercare.
        start_title (str): Il titolo di inizio.
        end_title (str): Il titolo di fine.

    Returns:
        str: Il testo tra i due titoli, o None se il testo trovato è nullo o i titoli non esistono.
    """
    # Usa regex per trovare i marcatori ignorando maiuscole/minuscole e spazi
    start_match = re.search(re.escape(start_title), text, re.IGNORECASE)
    end_match = re.search(re.escape(end_title), text, re.IGNORECASE)

    if not start_match or not end_match:
        print(f"Non è stato possibile trovare i titoli '{start_title}' o '{end_title}' nel testo.")
        return None

    start_index = start_match.end()  # Dopo il titolo di inizio
    end_index = end_match.start()  # Prima del titolo di fine

    # Estrae il testo tra i due titoli
    extracted_text = text[start_index:end_index].strip()

    # Controlla se il testo estratto è nullo
    if not extracted_text:
        return None

    return extracted_text


def extract_key_and_next_lines_as_string(text, key, num_lines=0, skip_lines=0):
    """
    Cerca una chiave nel testo estratto e restituisce una stringa unica con le righe successive alla chiave,
    saltando un certo numero di righe prima di iniziare l'estrazione.

    Args:
        pdf_path (str): Percorso del file PDF.
        key (str): La stringa da cercare come chiave.
        num_lines (int): Numero di righe successive da includere nel risultato (default: 5).
        skip_lines (int): Numero di righe da saltare dopo la chiave prima di iniziare l'estrazione (default: 0).

    Returns:
        str: Una stringa unica contenente le righe successive alla chiave, dopo aver saltato le righe specificate.
             Restituisce None se la chiave non viene trovata o se non ci sono righe sufficienti.
    """
    
    # Suddividi il testo in righe
    lines = text.splitlines()

    # Cerca la chiave nel testo
    for i, line in enumerate(lines):
        if key in line:
            # Prendi le righe successive alla chiave dopo aver saltato quelle specificate
            start_index = i + 1 + skip_lines  # Esclude la chiave e salta le righe
            next_lines = lines[start_index:start_index + num_lines]
            return "\n".join(next_lines).strip()  # Combina in una stringa unica

    # Se la chiave non viene trovata o non ci sono righe sufficienti
    return None

import re

def extract_number_or_date_after_key(text, key, search_type="both"):
    """
    Cerca una chiave nel testo estratto e restituisce il primo numero o data trovata successivamente alla chiave.
    Il numero o la data possono trovarsi sulla stessa riga della chiave o nelle righe successive.

    Args:
        pdf_path (str): Percorso del file PDF.
        key (str): La stringa da cercare come chiave.
        search_type (str): Specifica cosa cercare: "number" per numeri, "date" per date, o "both" per entrambi (default: "both").

    Returns:
        str: Il primo numero o data trovato successivamente alla chiave.
             Restituisce None se la chiave o il numero/data non vengono trovati.
    """

    # Suddividi il testo in righe
    lines = text.splitlines()

    # Flag per iniziare a cercare il numero o la data dopo la chiave
    found_key = False

    # Definisci i pattern per numeri e date
    if search_type == "number":
        pattern = re.compile(r'\b\d+(?:\.\d+)?\b')  # Solo numeri
    elif search_type == "date":
        pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')  # Solo date
    elif search_type == "both":
        pattern = re.compile(r'\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d+(?:\.\d+)?)\b')  # Numeri o date
    else:
        raise ValueError("search_type deve essere 'number', 'date' o 'both'")

    for line in lines:
        if found_key:
            # Cerca il primo numero o data nella riga
            match = pattern.search(line)
            if match:
                return match.group()  # Restituisci il numero o la data trovata

        if key in line:
            # Se troviamo la chiave, attiviamo il flag
            found_key = True
            # Cerca anche nella stessa riga della chiave
            match = pattern.search(line)
            if match:
                return match.group()  # Restituisci il numero o la data trovata

    # Se la chiave o il numero/data non vengono trovati
    return None


#Custom Function per estrarre dati di valore dalla perizia
def custom_data_extraction(pdf_path,numero_lotto):
    text = extract_text_from_pdf(pdf_path,numero_lotto)
    details = {}
    details['Valore di vendita giudiziaria'] = extract_number_or_date_after_key(text,'Valore di vendita giudiziaria','number')
    details['Conformità edilizia'] = extract_text_between_titles(text,'8.1. CONFORMITÀ EDILIZIA:','8.2')
    details['Conformità catastale'] = extract_text_between_titles(text,'8.2. CONFORMITÀ CATASTALE','8.3')
    details['Conformità urbanistica'] = extract_text_between_titles(text,'8.3. CONFORMITÀ URBANISTICA:','8.4')
    details['Corrispondenza catasto'] = extract_text_between_titles(text,'8.4. CORRISPONDENZA DATI CATASTALI/ATTO:','BENI IN')
    details['Superficie unità principali'] = extract_number_or_date_after_key(text,'Consistenza commerciale complessiva unità principali:','number')
    details['Superficie unità accessorie'] = extract_number_or_date_after_key(text,'Consistenza commerciale complessiva accessori:','number')
    details['Valore stato di fatto'] = extract_number_or_date_after_key(text,"Valore di Mercato dell'immobile nello stato di fatto e di diritto in cui si trova:",'number')
    details['Valore netto decurtazioni'] = extract_number_or_date_after_key(text,"Valore di realizzo dell'immobile al netto delle decurtazioni nello stato di",'number')
    details['Valore stato di diritto'] = extract_number_or_date_after_key(text,"Valore di vendita giudiziaria dell'immobile nello stato di fatto e di diritto in cui si",'number')
    details['Spese annue'] = extract_number_or_date_after_key(text,"Spese ordinarie annue di gestione dell'immobile:",'number')
    details['Spese annue deliberate'] = extract_number_or_date_after_key(text,"Spese straordinarie di gestione già deliberate ma non ancora scadute:",'number')
    details['Spese annue scadute'] = extract_number_or_date_after_key(text,"Spese condominiali scadute ed insolute alla data della perizia:",'number')
    details['Data valutazione'] = extract_number_or_date_after_key(text,'Data della valutazione:','date')
    return details

#Funzione per unire i due file di debug in uno unico per procedere all'importazione su database
def consolidate_json(name_file_aste, name_file_pdf, output_file):
    # Carica i dati JSON
    with open(name_file_aste, 'r', encoding='utf-8') as file_aste:
        data_aste = json.load(file_aste)

    with open(name_file_pdf, 'r', encoding='utf-8') as file_pdf:
        data_pdf = json.load(file_pdf)

    # Consolidare i dati
    consolidated_data = []

    if data_pdf:
        for asta in data_aste:
            pdf_data = next((pdf for pdf in data_pdf if pdf['auction_id'] == asta['auction_id']), {})
            consolidated_entry = {
                **asta,  # Tutti i campi di debug.json
                **pdf_data  # Tutti i campi di debug_pdf.json
            }
            consolidated_data.append(consolidated_entry)
    else:
        print("data_pdf è vuoto o None, impossibile procedere.")

    # Salva il file consolidato
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(consolidated_data, outfile, indent=4, ensure_ascii=False)

    print(f"Dati consolidati salvati in {output_file}")


 


