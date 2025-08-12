from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from google_sheets_scraper import GoogleSheetsRestaurantScraper
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Load environment variables
load_dotenv()

# Get config from environment variables
config = {
    'maps_api_key': os.getenv('MAPS_API_KEY'),
    'sheets_credentials': os.getenv('SHEETS_CREDENTIALS'),
    'spreadsheet_id': os.getenv('SPREADSHEET_ID')
}

# Initialize scraper
creds_path = None
if config['sheets_credentials'] and config['sheets_credentials'].strip():
    try:
        # Parse credentials from environment
        sheets_creds = json.loads(config['sheets_credentials'])
        # Save credentials to temp file
        creds_path = '/tmp/credentials.json'
        with open(creds_path, 'w') as f:
            json.dump(sheets_creds, f)
        print("Sheets credentials parsed successfully")
    except json.JSONDecodeError as e:
        print(f"Failed to parse SHEETS_CREDENTIALS: {e}")
        creds_path = None

# Scraper'ı başlat
scraper = GoogleSheetsRestaurantScraper(
    maps_api_key=config['maps_api_key'],
    sheets_credentials_path=creds_path,
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
        min_rating = data.get('minRating', 4.5)
        restaurant_name = data.get('restaurantName', None)
        page = data.get('page', 1)
        per_page = data.get('perPage', 20)
        
        # En az şehir ve (ilçe veya yemek türü veya restoran adı) gerekli
        if not city:
            return jsonify({
                "success": False,
                "error": "Şehir seçimi zorunludur"
            }), 400
        
        if not any([district, food_type, restaurant_name]):
            return jsonify({
                "success": False,
                "error": "İlçe, yemek türü veya restoran adından en az birini belirtmelisiniz"
            }), 400
        
        # Lokasyon oluştur
        if district:
            location = f"{district}, {city}"
        else:
            location = city
        
        # Yemek türü yoksa genel arama yap
        search_food_type = food_type if food_type else "restaurant"
        
        # Google Maps'te ara (Google Sheets'e kaydetmeden)
        all_restaurants = scraper.search_restaurants(location, search_food_type, min_rating=min_rating, restaurant_name=restaurant_name)
        
        # Pagination uygula
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        restaurants = all_restaurants[start_idx:end_idx]
        
        # Sonuçları döndür
        return jsonify({
            "success": True,
            "data": restaurants,
            "count": len(restaurants),
            "totalCount": len(all_restaurants),
            "page": page,
            "perPage": per_page,
            "hasMore": end_idx < len(all_restaurants),
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
        min_rating = data.get('minRating', 4.5)
        restaurant_name = data.get('restaurantName', None)
        save_to_sheets = data.get('saveToSheets', False)
        page = data.get('page', 1)
        per_page = data.get('perPage', 20)
        
        # En az şehir ve (ilçe veya yemek türü veya restoran adı) gerekli
        if not city:
            return jsonify({
                "success": False,
                "error": "Şehir seçimi zorunludur"
            }), 400
        
        if not any([district, food_type, restaurant_name]):
            return jsonify({
                "success": False,
                "error": "İlçe, yemek türü veya restoran adından en az birini belirtmelisiniz"
            }), 400
        
        # Lokasyon oluştur
        if district:
            location = f"{district}, {city}"
        else:
            location = city
        
        # Yemek türü yoksa genel arama yap
        search_food_type = food_type if food_type else "restaurant"
        
        if save_to_sheets:
            # Sheet adını oluştur
            sheet_parts = []
            if district:
                sheet_parts.append(district)
            if restaurant_name:
                sheet_parts.append(restaurant_name)
            if food_type:
                sheet_parts.append(food_type)
            sheet_parts.append(f"{min_rating}+")
            
            sheet_name = "_".join(sheet_parts)
            sheet_name = sheet_name.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
            
            # Ara ve kaydet
            result = scraper.run_search_to_sheets(location, search_food_type, sheet_name, min_rating=min_rating, restaurant_name=restaurant_name)
            
            # Kaydedilen restoranlari da getir
            all_restaurants = scraper.search_restaurants(location, search_food_type, min_rating=min_rating, restaurant_name=restaurant_name)
            
            # Pagination uygula
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            restaurants = all_restaurants[start_idx:end_idx]
            
            return jsonify({
                "success": result['success'],
                "data": restaurants,
                "count": len(restaurants),
                "totalCount": len(all_restaurants),
                "page": page,
                "perPage": per_page,
                "hasMore": end_idx < len(all_restaurants),
                "message": result['message'],
                "sheetName": sheet_name
            })
        else:
            # Sadece ara
            all_restaurants = scraper.search_restaurants(location, search_food_type, min_rating=min_rating, restaurant_name=restaurant_name)
            
            # Pagination uygula
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            restaurants = all_restaurants[start_idx:end_idx]
            
            return jsonify({
                "success": True,
                "data": restaurants,
                "count": len(restaurants),
                "totalCount": len(all_restaurants),
                "page": page,
                "perPage": per_page,
                "hasMore": end_idx < len(all_restaurants),
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
        'İstanbul': [
            'Adalar', 'Arnavutköy', 'Ataşehir', 'Avcılar', 'Bağcılar', 'Bahçelievler',
            'Bakırköy', 'Başakşehir', 'Bayrampaşa', 'Beşiktaş', 'Beykoz', 'Beylikdüzü',
            'Beyoğlu', 'Büyükçekmece', 'Çatalca', 'Çekmeköy', 'Esenler', 'Esenyurt',
            'Eyüpsultan', 'Fatih', 'Gaziosmanpaşa', 'Güngören', 'Kadıköy', 'Kağıthane',
            'Kartal', 'Küçükçekmece', 'Maltepe', 'Pendik', 'Sancaktepe', 'Sarıyer',
            'Silivri', 'Sultanbeyli', 'Sultangazi', 'Şile', 'Şişli', 'Tuzla',
            'Ümraniye', 'Üsküdar', 'Zeytinburnu'
        ],
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
        # Türk Mutfağı
        'köfteci', 'kebapçı', 'pideci', 'lahmacun', 'dönerci', 'iskender',
        'mantı', 'börekçi', 'gözlemeci', 'çiğ köfte', 'tantuni', 'kokoreç',
        'midyeci', 'kumru', 'lokanta', 'ev yemekleri', 'meyhane', 'ocakbaşı',
        'köfte', 'kebap', 'pide', 'türk mutfağı', 'anadolu mutfağı',
        
        # Deniz Ürünleri
        'balık', 'balık restoran', 'deniz ürünleri', 'mezeci', 'rakı balık',
        
        # Kahvaltı ve Serpme
        'kahvaltı', 'serpme kahvaltı', 'köy kahvaltısı', 'brunch', 'kafe',
        
        # Fast Food ve Dünya Mutfağı
        'burger', 'hamburger', 'pizza', 'döner', 'fast food', 'sokak lezzetleri',
        'sandviç', 'toast', 'wrap', 'waffle', 'kumpir',
        
        # Asya Mutfağı
        'sushi', 'japon', 'çin', 'uzak doğu', 'noodle', 'ramen', 'thai',
        'hint', 'kore', 'asya mutfağı', 'wok',
        
        # Avrupa Mutfağı
        'italyan', 'fransız', 'ispanyol', 'yunan', 'akdeniz', 'meksika',
        
        # Et Restoranları
        'steakhouse', 'kasap', 'mangal', 'et restoran', 'biftek',
        
        # Tatlı ve Fırın
        'tatlıcı', 'dondurmacı', 'pastane', 'fırın', 'bakery', 'cafe',
        'künefe', 'baklava', 'muhallebi', 'sütlaç', 'dondurma',
        
        # Vejeteryan ve Vegan
        'vegan', 'vejetaryen', 'sağlıklı', 'organik', 'salata',
        
        # İçecek ve Kafeler
        'kafeterya', 'kahve', 'coffee', 'bistro', 'pub', 'bar',
        
        # Özel Kategoriler
        'gurme', 'fine dining', 'butik restoran', 'bahçe restoran',
        'teras', 'sahil', 'boğaz', 'manzaralı'
    ]
    return jsonify(food_types)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
