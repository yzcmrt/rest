from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the api directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the scraper, but continue if it fails
try:
    from google_sheets_scraper import GoogleSheetsRestaurantScraper
except ImportError as e:
    logger.error(f"Failed to import GoogleSheetsRestaurantScraper: {e}")
    GoogleSheetsRestaurantScraper = None

# Initialize scraper
scraper = None
try:
    config = {
        'maps_api_key': os.environ.get('MAPS_API_KEY'),
        'sheets_credentials': os.environ.get('SHEETS_CREDENTIALS'),
        'spreadsheet_id': os.environ.get('SPREADSHEET_ID')
    }
    
    # If credentials are JSON string, parse it
    creds_path = None
    if config['sheets_credentials'] and config['sheets_credentials'].strip():
        try:
            # Clean the credentials string (remove extra whitespace/newlines)
            cleaned_creds = config['sheets_credentials'].strip()
            sheets_creds = json.loads(cleaned_creds)
            # Save credentials to temp file
            creds_path = '/tmp/credentials.json'
            with open(creds_path, 'w') as f:
                json.dump(sheets_creds, f)
            logger.info("Sheets credentials parsed successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SHEETS_CREDENTIALS: {e}")
            logger.error(f"First 100 chars of SHEETS_CREDENTIALS: {config['sheets_credentials'][:100]}...")
            creds_path = None
        
    # Initialize scraper
    if config['maps_api_key'] and GoogleSheetsRestaurantScraper:
        logger.info(f"Initializing scraper with Maps API key: {config['maps_api_key'][:10]}...")
        scraper = GoogleSheetsRestaurantScraper(
            maps_api_key=config['maps_api_key'],
            sheets_credentials_path=creds_path,
            spreadsheet_id=config['spreadsheet_id']
        )
        logger.info("Scraper initialized successfully")
    else:
        logger.error("Missing Maps API key or GoogleSheetsRestaurantScraper not available")
except Exception as e:
    logger.error(f"Config error: {e}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Handle CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            if not scraper:
                self.end_headers()
                response = {
                    "success": False,
                    "error": "API yapılandırması eksik. Lütfen environment variables kontrolü yapın."
                }
                self.wfile.write(json.dumps(response).encode())
                return
                
            city = data.get('city')
            district = data.get('district')
            food_type = data.get('foodType')
            min_rating = data.get('minRating', 4.5)
            restaurant_name = data.get('restaurantName', None)
            page = data.get('page', 1)
            per_page = data.get('perPage', 20)
            
            # En az şehir ve (ilçe veya yemek türü veya restoran adı) gerekli
            if not city:
                self.end_headers()
                response = {
                    "success": False,
                    "error": "Şehir seçimi zorunludur"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            if not any([district, food_type, restaurant_name]):
                self.end_headers()
                response = {
                    "success": False,
                    "error": "İlçe, yemek türü veya restoran adından en az birini belirtmelisiniz"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Lokasyon oluştur
            if district:
                location = f"{district}, {city}"
            else:
                location = city
            
            # Yemek türü yoksa genel arama yap
            search_food_type = food_type if food_type else "restaurant"
            
            all_restaurants = scraper.search_restaurants(location, search_food_type, min_rating=min_rating, restaurant_name=restaurant_name)
            
            # Pagination uygula
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            restaurants = all_restaurants[start_idx:end_idx]
            
            self.end_headers()
            response = {
                "success": True,
                "data": restaurants,
                "count": len(restaurants),
                "totalCount": len(all_restaurants),
                "page": page,
                "perPage": per_page,
                "hasMore": end_idx < len(all_restaurants),
                "location": location,
                "foodType": food_type
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.end_headers()
            response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(response).encode())
            
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
