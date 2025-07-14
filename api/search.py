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
    if config['sheets_credentials']:
        sheets_creds = json.loads(config['sheets_credentials'])
        # Save credentials to temp file
        creds_path = '/tmp/credentials.json'
        with open(creds_path, 'w') as f:
            json.dump(sheets_creds, f)
        
    # Initialize scraper
    if config['maps_api_key'] and GoogleSheetsRestaurantScraper:
        scraper = GoogleSheetsRestaurantScraper(
            maps_api_key=config['maps_api_key'],
            sheets_credentials_path=creds_path,
            spreadsheet_id=config['spreadsheet_id']
        )
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
            
            if not all([city, district, food_type]):
                self.end_headers()
                response = {
                    "success": False,
                    "error": "Şehir, ilçe ve yemek türü zorunludur"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            location = f"{district}, {city}"
            restaurants = scraper.search_restaurants(district, food_type)
            
            self.end_headers()
            response = {
                "success": True,
                "data": restaurants,
                "count": len(restaurants),
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
