import json
from google_sheets_scraper import GoogleSheetsRestaurantScraper

# Config dosyasını yükle
with open('config.json', 'r') as f:
    config = json.load(f)

# Scraper'ı başlat
scraper = GoogleSheetsRestaurantScraper(
    maps_api_key=config['maps_api_key'],
    sheets_credentials_path=config['sheets_credentials_path'],
    spreadsheet_id=config['spreadsheet_id']
)

# Tek arama örneği
def single_search():
    print("\n4.5+ puan filtresine sahip restoranlar aranıyor...")
    result = scraper.run_search_to_sheets("üsküdar", "köfteci", "Uskudar_Kofte_4.5+")
    print(f"Sonuç: {result}")

# Toplu arama örneği ilçe ve restorant türüne göre
def batch_search():
    print("\n4.5+ puan filtresine sahip restoranlar aranıyor...")
    searches = [
        {'location': 'üsküdar', 'restaurant_type': 'köfteci', 'sheet_name': 'Uskudar_Kofte_4.5+'},
        {'location': 'sarıyer', 'restaurant_type': 'kebapçı', 'sheet_name': 'Sariyer_Kebap_4.5+'},
        {'location': 'beşiktaş', 'restaurant_type': 'pideci', 'sheet_name': 'Besiktas_Pide_4.5+'}
    ]

    results = scraper.batch_search_to_sheets(searches)
    for result in results:
        print(f"{result['location']} - {result['restaurant_type']}: {result['result']}")

if __name__ == "__main__":
    print("1. Tek arama")
    print("2. Toplu arama")
    choice = input("Seçiminiz (1/2): ")

    if choice == "1":
        single_search()
    elif choice == "2":
        batch_search()
