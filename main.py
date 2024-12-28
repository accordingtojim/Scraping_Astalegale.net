from scraping import fetch_html_with_cookies, extract_auction_links_from_page,extract_auction_details,ask_user
import json
import argparse  # Aggiunto argparse
import os
from sqlite_import import import_json_to_sqlite
from analyzing_pdf import custom_data_extraction,consolidate_json
auctions = []
enhanced_auctions = []
save_directory = "downloads"
name_dump = 'debug.json'


if 1:
    execute_download = ask_user()
    #Se passi 'all' ti scarica tutti i links di tutte le pagine che trova
    links_so = extract_auction_links_from_page("residenziali","so","lombardia",'all')
    links_va = extract_auction_links_from_page("residenziali","va","lombardia",'all')
    links_vc = extract_auction_links_from_page("residenziali","vc","piemonte",'all')
    links_vb = extract_auction_links_from_page("residenziali","vb","piemonte",'all')
    links = links_so +links_vc+links_vb+links_va


    for link in links: auctions.append(extract_auction_details(link,'downloads',execute_download))

    #Debug
    with open(f"{name_dump}", 'w', encoding='utf-8') as file:
        json.dump(auctions, file, indent=4, ensure_ascii=False)

    #Per ogni asta estraggo dati dalla perizia e esporto in un json per debug
    for auction in auctions:
        
        directory = auction.get("Directory")
        auction_id = auction.get("auction_id")
        lotto = auction.get("Lotto")
        enhanced_data = {"auction_id": auction_id}  # Inizializza con auction_id
        if directory:
            perizia_path = os.path.join(directory, "perizia_1.pdf")
            if os.path.exists(perizia_path):
                extracted_data = custom_data_extraction(perizia_path,lotto)
                enhanced_data.update(extracted_data)
        enhanced_auctions.append(enhanced_data)

    #debug
    with open("debug_pdf.json", 'w', encoding='utf-8') as file:
        json.dump(enhanced_auctions, file, indent=4, ensure_ascii=False)

    #unisco i due json per avere un json unico da importare in sqlite
    consolidate_json('debug.json','debug_pdf.json','final.json')

#importo dati in sqlite
import_json_to_sqlite('final.json', 'aste.db')


    
