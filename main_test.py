from scraping import fetch_html, extract_auction_links_from_page,extract_auction_details
import json
import argparse  # Aggiunto argparse
import os
from sqlite_import import import_json_to_sqlite
from analyzing_pdf import custom_data_extraction,consolidate_json

auctions = []
enhanced_auctions = []
save_directory = "downloads"
name_dump = 'debug.json'


links_va = extract_auction_links_from_page("residenziali","va","lombardia",2)
#links_so = extract_auction_links_from_page("residenziali","so","lombardia",1)
#test = links_va + links_so

for link in links_va:
    auctions.append(extract_auction_details(link,'downloads'))

#Debug
with open(f"{name_dump}", 'w', encoding='utf-8') as file:
    json.dump(auctions, file, indent=4, ensure_ascii=False)

#Per ogni asta estraggo dati dalla perizia e esporto in un json per debug
for auction in auctions:
    if auction is not None:
        print(auction.get('URL', 'URL non trovato'))

        directory = auction.get("Directory")
        auction_id = auction.get("auction_id")
        lotto = auction.get("Lotto")
        enhanced_data = {"auction_id": auction_id}  # Inizializza con auction_id

        if directory:
            perizia_path = os.path.join(directory, "perizia_1.pdf")
            if os.path.exists(perizia_path):
                extracted_data = custom_data_extraction(perizia_path, lotto)
                enhanced_data.update(extracted_data)

        enhanced_auctions.append(enhanced_data)
    else:
        print(f"Errore: l'asta per il link {link} non è stata estratta correttamente.")

#debug final
with open("debug_pdf.json", 'w', encoding='utf-8') as file:
    json.dump(enhanced_auctions, file, indent=4, ensure_ascii=False)

#unisco i due json per avere un json unico da importare in sqlite
consolidate_json('debug.json','debug_pdf.json','final.json')

#importo dati in sqlite
import_json_to_sqlite('final.json', 'aste.db')


    
