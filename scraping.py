import requests
import math
from bs4 import BeautifulSoup
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import mimetypes
import re
import tkinter as tk
from tkinter import messagebox
from requests.exceptions import RequestException
import time
from datetime import datetime

# da riga 12 a 21 può essere anche sostituito semplicemente da do_download = 1
def ask_user():
    root = tk.Tk()
    root.withdraw()  # Nasconde la finestra principale
    # Mostra la finestra di dialogo con le opzioni 'Yes' e 'No'
    response = messagebox.askyesno("Conferma Download", "Vuoi eseguire i download?")
    # Se l'utente seleziona 'Yes', assegna 1 a do_download, altrimenti assegna 0
    do_download = 1 if response else 0
    return do_download



def load_province_map(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            province_map = json.load(file)
        return province_map
    except FileNotFoundError:
        print(f"Errore: il file {json_file_path} non è stato trovato.")
        return {}
    except json.JSONDecodeError:
        print(f"Errore: il file {json_file_path} non contiene un JSON valido.")
        return {}

# Funzione di supporto per pulire il campo "Offerta Minima" (rimuove il "(1)")
def clean_prezzi(value):
    if value:
        # Rimuove anazioni come "(1)", "(2)", ecc.
        cleaned = re.sub(r'\(\d+\)', '', value).strip()  # Modificato per rimuovere numeri tra parentesi
        # Rimuove simboli monetari come '€'
        cleaned = re.sub(r'[^\d,\.]', '', cleaned).strip()  # Mantiene solo numeri, virgola e punto
        # Rimuove il punto come separatore delle migliaia
        cleaned = cleaned.replace('.', '')  # Rimuove il punto
        #Sostituisci virgola con punto per delimitare decimali
        cleaned = cleaned.replace(',', '.')
        if cleaned != '':
        #transformo in float e arrotonda
            cleaned = round(float(cleaned))
        else:
            cleaned = 1
        return cleaned
    return 1    
    

# Carica la mappa delle province dal file JSON
province_map = load_province_map('mappe_province.json')

def fetch_html_with_cookies(url, headers=None, proxies=None):
    """
    Scarica il contenuto HTML di una pagina specificata dall'URL.

    :param url: URL della pagina da scaricare.
    :param headers: Dizionario con gli headers da usare nella richiesta (opzionale).
    :param proxies: Dizionario con i proxy da usare nella richiesta (opzionale).
    :return: Contenuto HTML della pagina o None in caso di errore.
    """
    # Headers di default (se non specificati)
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    # Usa gli headers forniti o quelli di default
    headers = headers or default_headers
    time.sleep(2) 
    try:
        session = requests.Session()  # Usa una sessione persistente
        response = session.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()  # Solleva eccezioni per errori HTTP
        return response.text
    except RequestException as e:
        print(f"Errore durante il fetch: {e}")
        return None

#Funzione per capire max numero di pagine per categoria
def get_total_pages(html_content):
    """
    Estrae il numero totale di pagine dal contenuto HTML di una pagina web.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    pagination = soup.find('ul', class_='pagination')
    if not pagination:
        print("⚠️ Nessun elemento di paginazione trovato!")
        return 0

    # Cerca tutti i pulsanti all'interno della paginazione
    page_numbers = []
    for page_item in pagination.find_all('li', class_='page-item'):
        button = page_item.find('button', class_='page-link')
        if button and button.text.isdigit():  # Verifica se il testo è un numero
            page_numbers.append(int(button.text))

    if page_numbers:
        return max(page_numbers)  # Restituisce il numero massimo trovato
    else:
        print("⚠️ Nessun numero di pagina trovato!")
        return 0

#prima di numero di pagina = 1 ho aggiunto codice per stampare max n pagine per categoria
# Funzione per estrarre i link delle aste Generale
# Funzione per estrarre i link delle aste da tutte le pagine
def extract_auction_links_from_page(categoria, provincia, regione, max_pagina):
    links = set()  # Usiamo un set per evitare duplicati

    # Ottieni il contenuto HTML della prima pagina per calcolare il totale delle pagine
    first_page_url = f"https://www.astalegale.net/Immobili?categories={categoria}&page=1&province={provincia}&regioni={regione}&sort=DataPubblicazioneDesc"
    print(f"Scaricando: {first_page_url}")

    first_page_html = fetch_html_with_cookies(first_page_url)
    if not first_page_html:
        print("⚠️ Impossibile scaricare la prima pagina!")
        return []

    # Calcola il numero massimo di pagine e lo stampa
    total_pages = get_total_pages(first_page_html)
    print(f"Questa categoria ha {total_pages} pagine.")

    numero_pagina = 1
    while True:
        website_url = f"https://www.astalegale.net/Immobili?categories={categoria}&page={numero_pagina}&province={provincia}&regioni={regione}&sort=DataPubblicazioneDesc"
        print(f"Scaricando: {website_url}")
        
        html_content = fetch_html_with_cookies(website_url)
        if html_content is None:
            print(f"⚠️ Contenuto HTML vuoto per pagina {numero_pagina}. Passo alla successiva.")
            if max_pagina != 'all':
                break  # Esce dal loop se non stiamo scaricando tutte le pagine
            else:
                numero_pagina += 1
                continue
        else:
            soup = BeautifulSoup(html_content, 'html.parser')

        # Cerca i div con classe card-header
        page_links_found = False
        for card_header in soup.find_all('div', class_='card-header'):
            # Trova il primo link all'interno di card-header
            a_tag = card_header.find('a', href=True)
            if a_tag:
                relative_url = a_tag.get('href')
                if relative_url.startswith('/'):  # Verifichiamo che sia un URL relativo
                    full_url = "https://www.astalegale.net" + relative_url
                else:
                    full_url = relative_url
                links.add(full_url)  # Usiamo il set per evitare duplicati
                page_links_found = True

        if not page_links_found and max_pagina == 'all':
            print(f"Nessun link trovato alla pagina {numero_pagina}. Presumo che non ci siano altre pagine.")
            break

        print(f"Pagina {numero_pagina} completata. Link trovati finora: {len(links)}")

        if max_pagina != 'all' and numero_pagina >= max_pagina:
            break

        
        numero_pagina += 1

    return list(links)  # Convertiamo il set in una lista prima di restituirlo


def extract_auction_details(url, save_directory,execute_download):

    
    # Funzione di supporto per correggere la data
    def clean_DateTime(date_str):    
        try:
            # Attempt to parse the date string in DD/MM/YYYY format
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            # If successful, reformat to YYYY/MM/DD
            return date_obj.strftime('%Y/%m/%d')
        except ValueError:
            # If parsing fails, return the original date string
            return date_str
        
        # Funzione di supporto per correggere il valore del lotto
    def clean_lotto(value):
        value = value.strip().lower()
        return "1" if value in ["unico", "LOTTO UNICO", "lotto unico"] else value
    
    # Funzione di supporto per correggere lo stato di occupazione
    def clean_stato_occupazione(value):
        return stato_occupazione_map.get(value.upper(), value) if value else None
        
    html_content = fetch_html_with_cookies(url)
    if html_content == None:
        return None
    soup = BeautifulSoup(html_content, 'html.parser')
    
       #Deubg Test
    with open("html.json", 'w', encoding='utf-8') as file:
        json.dump(html_content, file, indent=4, ensure_ascii=False)

    # Funzione di supporto per cercare elementi con testo flessibile
    def find_flexible_text(tag, text):
        return soup.find(tag, text=lambda t: t and text in t)
    
    # Estrazione della via
    # In questo HTML, la via è contenuta nell'elemento <h2> all'interno del div con classe "dettaglio_title"
    via_container = soup.find('div', class_='dettaglio_title')
    via_element = via_container.find('h2') if via_container else None
    via = via_element.text.strip() if via_element else 'Via non trovata'

    # Estrazione del comune
    # In questo HTML, il comune è contenuto nello <span> con l'attributo md-value="città e provincia"
    comune_container = soup.find('div', class_='dettaglio_luogo')
    comune_element = comune_container.find('span', {'md-value': 'città e provincia'}) if comune_container else None
    comune_text = comune_element.text.strip() if comune_element else 'Comune non trovato'
    # Se vuoi ottenere solo il nome del comune (senza la sigla tra parentesi), puoi dividere la stringa:
    comune = comune_text.split('(')[0].strip()

    # Estrazione della provincia
    if '(' in comune_text and ')' in comune_text:
        provincia_sigla = comune_text.split('(')[1].split(')')[0].strip()
    else:
        provincia = "Provincia non trovata"
    provincia = province_map.get(provincia_sigla, "Provincia non trovata")

    # Indirizzo ------------------------ rivedere che indirizzo è
    indirizzo_element = soup.find('span', {'data-pn-indirizzo-via': 'val'})
    indirizzo = indirizzo_element.text.strip() if indirizzo_element else 'Indirizzo non trovato'

    # Extract Lotto
    lotto_element = soup.find("span", {"data-pn-lotto-codice": "val"})
    lotto = lotto_element.text.strip() if lotto_element else "Lotto non trovato"

    # Extract Categoria
    categoria_element = soup.find("span", {"md-value": "categoria"})
    categoria = categoria_element.text.strip() if categoria_element else "Categoria non trovata"
    
    # Categoria Ministeriale - non più usata
    categoria_min_element = soup.find('span', text='Categoria Ministeriale')
    if categoria_min_element:
        categoria_min_value = categoria_min_element.find_next_sibling('span')
        categoria_ministeriale = categoria_min_value.text.strip() if categoria_min_value else 'Categoria ministeriale non trovata'
    else:
        categoria_ministeriale = 'Categoria ministeriale non trovata'
    
    # Valore di stima -------- da rimuovere
    # valore_stima_element = soup.find('span', text='Valore di stima')
    # valore_stima_value = valore_stima_element.find_next_sibling('span') if valore_stima_element else None
    # valore_stima = clean_prezzi(valore_stima_value.text.strip() if valore_stima_value else 'Valore di stima non trovato')
    
    # Tipologia
    tipologia_element = soup.find("span", {"md-value": "tipologia vendita"})
    tipologia = tipologia_element.text.strip() if tipologia_element else "Tipologia non trovata"

    # Prezzo
    prezzo_element = soup.find("span", {"md-value": "Prezzo base"})
    prezzo = prezzo_element.text.strip() if prezzo_element else "Prezzo non trovato"

    # Termine presentazione offerte
    termine_offerte_element = soup.find("span", {"md-value": "termine presentazione offerte"})
    termine_offerte = termine_offerte_element.text.strip() if termine_offerte_element else "Termine presentazione offerte non trovato"
    
    # Rimuovere l'orario dal termine presentazione offerte (manteniamo solo la data)
    # Metodo con split
    termine_offerte_data = termine_offerte.split(' ')[0] if termine_offerte != 'Termine presentazione offerte non trovato' else termine_offerte

    # Data asta
    data_asta_element = soup.find("span", {"md-value": "Data Asta"})
    data_asta = data_asta_element.text.strip() if data_asta_element else "Data asta non trovata"

    # Rimuovere l'orario dal termine data (manteniamo solo la data)
    # Metodo con split
    data_asta_data = data_asta.split(' ')[0] if data_asta != 'Termine presentazione offerte non trovato' else data_asta
    data_asta_data = clean_DateTime(data_asta_data)

    # Offerta minima
    offerta_min_element = soup.find("span", {"md-value": "offerta minima"})
    offerta_min = offerta_min_element.text.strip() if offerta_min_element else "Offerta minima non trovata"

    # Modalità gara
    modalita_gara_element = soup.find("span", {"md-value": "modalità gara"})
    modalita_gara = modalita_gara_element.text.strip() if modalita_gara_element else "Modalità gara non trovata"

    # Mappa di correzione per lo stato di occupazione
    stato_occupazione_map = {
        "LIBER": "Libero",
        "OCCUPATO": "Occupato",
        "OCCUPAT": "Occupato",
        "OCCUPATO DA TERZI CON TITOLO": "Occupato da terzi con titolo",
        "OCCUPATO DA DEBITORE/FAMIGLIA": "Occupato da debitore/famiglia",
        # Aggiungi altre mappature se necessario
    }

    

    # Estrarre e pulire lo stato di occupazione
    # Locate the label span with exact text
    stato_occupazione_element = soup.find('span', string='Stato di occupazione:')

    # Extract the next relevant span
    stato_occupazione_value = stato_occupazione_element.find_next_sibling('span', attrs={'data-pn-bene-immobile-disp': 'val'}) if stato_occupazione_element else None
    stato_occupazione = clean_stato_occupazione(stato_occupazione_value.text.strip() if stato_occupazione_value else 'Stato occupazione non trovato')

    # Extract auction history
    storico_aste = []
    storico_container = soup.find('ul', class_='storico')

    if storico_container:
        for item in storico_container.find_all('li'):
            # Extract date (either inside <span> or <a>)
            data_element = item.find('span', class_='storico-data') or item.find('a', class_='storico-data')
            data = data_element.text.strip() if data_element else 'Data non trovata'

            # Extract auction price (always last <span> in <li>)
            prezzo_element_storico = item.find_all('span')[-1] if item.find_all('span') else None
            prezzo_storico = prezzo_element_storico.text.strip() if prezzo_element_storico else 'Prezzo non trovato'

            storico_aste.append({'data': data, 'prezzo': prezzo_storico})

    # Calcolo del numero di aste andate vuote
    numero_aste_vuote = len(storico_aste)

    #Indicatore stima/offerta minima
    kpi_sconto_long = float(offerta_min) / float(prezzo)
    kpi_sconto = math.trunc(kpi_sconto_long * 100) / 100
    kpi_sconto_threshold = 0.65

    #indicatore interessante
    if kpi_sconto < kpi_sconto_threshold and stato_occupazione == "Libero" and numero_aste_vuote < 5:
        interessante = "1"
    else:
        interessante = ""
#---------------------------------------------------------------------
    auction_id = f"asta_{via.replace('-', '').replace('  ', ' ').replace(' ', '_')}_{comune.replace('-', '').replace('  ', ' ').replace(' ', '_')}"
    auction_id = auction_id + "_" + str(lotto)
    url = f"{url}"
    details = {
        'interessante':interessante,
        'auction_id': auction_id,
        'kpi_sconto': kpi_sconto,
        'via': via,
        'comune': comune,
        'provincia': provincia, 
        'Indirizzo': indirizzo,
        'Tipologia': tipologia,
        #'Valore di Stima': valore_stima,
        'Prezzo': prezzo,
        'Offerta Minima': offerta_min,
        'Categoria': categoria,
        'Stato di Occupazione': stato_occupazione,
        'Data Asta': data_asta_data,
        'Lotto': lotto, 
        'Numero Aste Vuote': numero_aste_vuote,
        #'Categoria Ministeriale': categoria_ministeriale,
        'Termine presentazione offerte': termine_offerte_data,
        #'Fine iscrizioni': fine_iscrizioni,  
        'Modalità Gara': modalita_gara,
        'Storico Aste': storico_aste,
        'URL': url,
        'Directory': os.path.join(save_directory, auction_id)
    }

    # Crea la directory specifica per l'asta se non esiste
    if not os.path.exists(details['Directory']):
        os.makedirs(details['Directory'])

    # Cerca i link ai file nel nuovo formato HTML
    if execute_download == 1:
        document_container = soup.find('ul', class_='documenti d-flex flex-wrap')
        if not document_container:
            print("Nessun documento trovato nella pagina.")
            return
    
        links = document_container.find_all('a', href=True)
        
        #Deubg Test
    with open("html.json", 'w', encoding='utf-8') as file:
        json.dump(links, file, indent=4, ensure_ascii=False)

     # Dizionario per tenere traccia dei conteggi dei file
        file_counters = {'planimetria': 0, 'ordinanza': 0, 'perizia': 0, 'avviso': 0}
        with ThreadPoolExecutor(max_workers=6) as executor:  # Puoi modificare max_workers per regolare il grado di parallelismo
            futures = []
            for link in links:
                href = link['href']
                link_text = link.text.lower()
                # Determina il tipo di file in base al testo del link
                file_type = None
                for keyword in file_counters.keys():
                    if keyword in link_text:
                        file_type = keyword
                        break

                if file_type:
                    # Aggiorna il contatore e crea il nome file con numero progressivo
                    file_counters[file_type] += 1
                    file_name = f"{file_type}_{file_counters[file_type]}.pdf"
                    file_url = href if href.startswith('http') else "https://documents.astalegale.net" + href
                    file_path = os.path.join(details['Directory'], file_name)

                    # Funzione diretta per il download
                    futures.append(
                        executor.submit(
                            lambda url, path:
                            download_file(url, path),
                            file_url,
                            file_path
                        )
                    )

            for future in as_completed(futures):
                try:
                    future.result()  # Controlla eventuali eccezioni nel thread
                except Exception as e:
                    print(f"Errore durante il download di un file: {e}")
    return details

def download_files_from_page(url, auction_directory):
    """Scarica tutti i file da una pagina di un'asta in multithreading."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"Errore durante il download della pagina: {e}")
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')

    # Crea la directory specifica per l'asta se non esiste
    if not os.path.exists(auction_directory):
        os.makedirs(auction_directory)

    # Cerca i link ai file nel nuovo formato HTML
    document_container = soup.find('ul', class_='documenti d-flex flex-wrap')
    if not document_container:
        print("Nessun documento trovato nella pagina.")
        return
    
    links = document_container.find_all('a', href=True)
    
    #Deubg Test
    with open("html.json", 'w', encoding='utf-8') as file:
        json.dump(soup, file, indent=4, ensure_ascii=False)
        
    with ThreadPoolExecutor(max_workers=2) as executor:  # Puoi modificare max_workers per regolare il grado di parallelismo
        futures = []
        for link in links:
            href = link['href']
            link_text = link.text.lower()
            if any(keyword in link_text for keyword in ["planimetria", "ordinanza", "perizia", "avviso"]):
                file_name = href.split('/')[-1]
                file_url = href if href.startswith('http') else "https://documents.astalegale.net" + href
                file_path = os.path.join(auction_directory, file_name)

                # Funzione diretta per il download
                futures.append(
                    executor.submit(
                        lambda url, path: 
                        download_file(url, path), 
                        file_url, 
                        file_path
                    )
                )

        for future in as_completed(futures):
            try:
                future.result()  # Controlla eventuali eccezioni nel thread
            except Exception as e:
                print(f"Errore durante il download di un file: {e}")

def download_file(file_url, file_path):
    """Scarica e salva un singolo file, aggiunge l'estensione se mancante e gestisce la rimozione di duplicati."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        session = requests.Session()  # Usa una sessione persistente
        print(f"Scaricando {file_path} da: {file_url}")
        
        file_response = session.get(file_url, headers=headers, stream=True)
        file_response.raise_for_status()
        
        # Ottieni il content-type e determina l'estensione
        content_type = file_response.headers.get('Content-Type', '')
        guessed_extension = mimetypes.guess_extension(content_type)
        
        # Se il file_path non ha un'estensione, usiamo quella rilevata
        if '.' not in os.path.basename(file_path) and guessed_extension:
            file_path_with_extension = file_path + guessed_extension
        elif not file_path.endswith(('.pdf', '.jpg', '.png', '.docx', '.xlsx')) and guessed_extension:
            file_path_with_extension = file_path + guessed_extension
        else:
            file_path_with_extension = file_path
        
        # Se il file con estensione esiste, non lo scarichiamo di nuovo
        if os.path.exists(file_path_with_extension):
            print(f"❌ File già esistente: {file_path_with_extension}, download saltato.")
            return

        with open(file_path_with_extension, 'wb') as file:
            for chunk in file_response.iter_content(chunk_size=1024):
                file.write(chunk)
        
        print(f"✅ File salvato in: {file_path_with_extension}")
        
        # Elimina il file senza estensione se esiste
        if file_path != file_path_with_extension and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️ File duplicato rimosso: {file_path}")
            except Exception as e:
                print(f"⚠️ Errore durante la rimozione del file duplicato {file_path}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore durante il download del file {file_path}: {e}")



def download_files_for_all_auctions(auction, save_directory="downloads"):
    """Scarica i file per tutte le aste, eseguendo il download delle pagine e dei file in multithreading."""
    indirizzo = auction['Indirizzo']
    comune = auction['Comune']
    auction_url = auction['URL']
    directory_name = f"{indirizzo}_{comune}" if indirizzo != 'Indirizzo non trovato' else "asta_generica"
    auction.update({'Directory_name': directory_name})
    auction_directory = os.path.join(save_directory, directory_name)

    asteannuncio_url = auction_url.replace("www.canaleaste.it", "www.asteannunci.it")
    print(f"Scaricando i file per l'asta: {asteannuncio_url}")

    download_files_from_page(asteannuncio_url, auction_directory)


        


        
        

