import json
import os
from google_sheets_scraper import GoogleSheetsRestaurantScraper

# Script'in bulunduğu dizini al
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Config dosyasını yükle
config_path = os.path.join(SCRIPT_DIR, 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Scraper'ı başlat
scraper = GoogleSheetsRestaurantScraper(
    maps_api_key=config['maps_api_key'],
    sheets_credentials_path=os.path.join(SCRIPT_DIR, config['sheets_credentials_path']),
    spreadsheet_id=config['spreadsheet_id']
)

# Özel arama fonksiyonu
def custom_search():
    print("\n=== Özel Restoran Araması ===")
    print("4.5+ puan filtresine sahip restoranlar aranacak\n")
    
    location = input("İlçe adını girin (örn: beşiktaş, üsküdar, kadıköy): ").strip()
    restaurant_type = input("Restoran türünü girin (örn: dondurmacı, köfteci, kebapçı): ").strip()
    
    # Sheet adını otomatik oluştur
    sheet_name = f"{location.title()}_{restaurant_type.title()}_4.5+"
    sheet_name = sheet_name.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    
    print(f"\nAranıyor: {location} bölgesinde {restaurant_type}")
    print(f"Sheet adı: {sheet_name}")
    
    result = scraper.run_search_to_sheets(location, restaurant_type, sheet_name)
    print(f"\nSonuç: {result}")

# Çoklu özel arama
def multiple_custom_search():
    print("\n=== Çoklu Özel Restoran Araması ===")
    print("4.5+ puan filtresine sahip restoranlar aranacak")
    print("Aramalarınızı ekleyin. Bitirmek için boş bırakıp Enter'a basın.\n")
    
    searches = []
    while True:
        location = input("İlçe adını girin (bitirmek için boş bırakın): ").strip()
        if not location:
            break
            
        restaurant_type = input("Restoran türünü girin: ").strip()
        
        # Sheet adını otomatik oluştur
        sheet_name = f"{location.title()}_{restaurant_type.title()}_4.5+"
        sheet_name = sheet_name.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
        
        searches.append({
            'location': location,
            'restaurant_type': restaurant_type,
            'sheet_name': sheet_name
        })
        print(f"Eklendi: {location} - {restaurant_type}\n")
    
    if searches:
        print(f"\nToplam {len(searches)} arama yapılacak...")
        results = scraper.batch_search_to_sheets(searches)
        
        print("\n=== Sonuçlar ===")
        for result in results:
            print(f"{result['location']} - {result['restaurant_type']}: {result['result']}")
    else:
        print("Hiç arama eklenmedi.")

# Hazır örnekler
def predefined_searches():
    print("\n=== Hazır Arama Örnekleri ===")
    print("4.5+ puan filtresine sahip restoranlar aranacak\n")
    
    searches = [
        {'location': 'üsküdar', 'restaurant_type': 'köfteci', 'sheet_name': 'Uskudar_Kofte_4.5+'},
        {'location': 'sarıyer', 'restaurant_type': 'kebapçı', 'sheet_name': 'Sariyer_Kebap_4.5+'},
        {'location': 'beşiktaş', 'restaurant_type': 'pideci', 'sheet_name': 'Besiktas_Pide_4.5+'},
        {'location': 'beşiktaş', 'restaurant_type': 'dondurmacı', 'sheet_name': 'Besiktas_Dondurma_4.5+'},
        {'location': 'kadıköy', 'restaurant_type': 'balık', 'sheet_name': 'Kadikoy_Balik_4.5+'}
    ]
    
    print("Aranacak yerler:")
    for i, search in enumerate(searches, 1):
        print(f"{i}. {search['location']} - {search['restaurant_type']}")
    
    confirm = input("\nDevam etmek istiyor musunuz? (e/h): ")
    if confirm.lower() == 'e':
        results = scraper.batch_search_to_sheets(searches)
        
        print("\n=== Sonuçlar ===")
        for result in results:
            print(f"{result['location']} - {result['restaurant_type']}: {result['result']}")

if __name__ == "__main__":
    print("=== Google Maps Restoran Scraper ===")
    print("Tüm aramalar 4.5+ puan filtresine sahiptir\n")
    print("1. Tek özel arama")
    print("2. Çoklu özel arama")
    print("3. Hazır arama örnekleri")
    
    choice = input("\nSeçiminiz (1/2/3): ")
    
    if choice == "1":
        custom_search()
    elif choice == "2":
        multiple_custom_search()
    elif choice == "3":
        predefined_searches()
    else:
        print("Geçersiz seçim!")
