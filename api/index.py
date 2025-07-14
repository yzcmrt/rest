from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from google_sheets_scraper import GoogleSheetsRestaurantScraper

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Script'in bulunduğu dizini al
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Config dosyasını yükle
config_path = os.path.join(SCRIPT_DIR, '../backend/config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Scraper'ı başlat
scraper = GoogleSheetsRestaurantScraper(
    maps_api_key=config['maps_api_key'],
    sheets_credentials_path=os.path.join(SCRIPT_DIR, '../backend', config['sheets_credentials_path']),
    spreadsheet_id=config['spreadsheet_id']
)

@app.route('/api/health', methods=['GET'])
def health_check():
    """API sağlık kontrolü"""
    return jsonify({"status": "healthy", "message": "Restaurant Scraper API is running"})

@app.route('/api/search', methods=['POST'])
def search_restaurants():
    """Restoran arama endpoint'i"""
    try:
        data = request.get_json()
        
        # Parametreleri al
        city = data.get('city')
        district = data.get('district')
        food_type = data.get('foodType')
        
        if not all([city, district, food_type]):
            return jsonify({
                "success": False,
                "error": "Şehir, ilçe ve yemek türü zorunludur"
            }), 400
        
        # Lokasyon oluştur
        location = f"{district}, {city}"
        
        # Google Maps'te ara (Google Sheets'e kaydetmeden)
        restaurants = scraper.search_restaurants(district, food_type)
        
        # Sonuçları döndür
        return jsonify({
            "success": True,
            "data": restaurants,
            "count": len(restaurants),
            "location": location,
            "foodType": food_type
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/search-and-save', methods=['POST'])
def search_and_save_restaurants():
    """Restoran ara ve Google Sheets'e kaydet"""
    try:
        data = request.get_json()
        
        # Parametreleri al
        city = data.get('city')
        district = data.get('district')
        food_type = data.get('foodType')
        save_to_sheets = data.get('saveToSheets', False)
        
        if not all([city, district, food_type]):
            return jsonify({
                "success": False,
                "error": "Şehir, ilçe ve yemek türü zorunludur"
            }), 400
        
        # Lokasyon oluştur
        location = f"{district}, {city}"
        
        if save_to_sheets:
            # Sheet adını oluştur
            sheet_name = f"{district}_{food_type}_4.5+"
            sheet_name = sheet_name.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
            
            # Ara ve kaydet
            result = scraper.run_search_to_sheets(district, food_type, sheet_name)
            
            # Kaydedilen restoranları da getir
            restaurants = scraper.search_restaurants(district, food_type)
            
            return jsonify({
                "success": result['success'],
                "data": restaurants,
                "count": result['count'],
                "message": result['message'],
                "sheetName": sheet_name
            })
        else:
            # Sadece ara
            restaurants = scraper.search_restaurants(district, food_type)
            
            return jsonify({
                "success": True,
                "data": restaurants,
                "count": len(restaurants),
                "location": location,
                "foodType": food_type
            })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Desteklenen şehirleri döndür"""
    cities = {
        'İstanbul': ['Üsküdar', 'Kadıköy', 'Beşiktaş', 'Sarıyer', 'Şişli', 'Fatih', 'Beyoğlu', 'Bakırköy', 'Maltepe', 'Pendik', 'Ataşehir', 'Kartal', 'Tuzla', 'Sultanbeyli', 'Sancaktepe'],
        'Ankara': ['Çankaya', 'Keçiören', 'Mamak', 'Altındağ', 'Yenimahalle', 'Etimesgut', 'Sincan', 'Pursaklar', 'Gölbaşı', 'Polatlı'],
        'İzmir': ['Karşıyaka', 'Bornova', 'Konak', 'Çeşme', 'Alsancak', 'Buca', 'Bayraklı', 'Karabağlar', 'Balçova', 'Narlıdere'],
        'Bursa': ['Nilüfer', 'Osmangazi', 'Yıldırım', 'Gürsu', 'Mudanya', 'Gemlik', 'İnegöl', 'Kestel'],
        'Antalya': ['Muratpaşa', 'Kepez', 'Konyaaltı', 'Alanya', 'Manavgat', 'Serik', 'Aksu', 'Döşemealtı'],
        'Adana': ['Seyhan', 'Yüreğir', 'Çukurova', 'Sarıçam', 'Karaisalı'],
        'Trabzon': ['Ortahisar', 'Akçaabat', 'Yomra', 'Arsin', 'Araklı'],
        'Eskişehir': ['Odunpazarı', 'Tepebaşı', 'Alpu', 'Beylikova', 'Çifteler']
    }
    return jsonify(cities)

@app.route('/api/food-types', methods=['GET'])
def get_food_types():
    """Desteklenen yemek türlerini döndür"""
    food_types = [
        'köfteci', 'kebapçı', 'pideci', 'dondurmacı', 'balık', 
        'kahvaltı', 'burger', 'pizza', 'mantı', 'dönerci',
        'lokanta', 'börekçi', 'tatlıcı', 'kafeterya', 'steakhouse',
        'çiğ köfte', 'tantuni', 'kokoreç', 'midyeci', 'kumru'
    ]
    return jsonify(food_types)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

