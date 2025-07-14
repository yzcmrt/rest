import googlemaps
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from datetime import datetime
import time

# Logging ayarı
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GoogleSheetsRestaurantScraper:
    def __init__(self, maps_api_key, sheets_credentials_path=None, spreadsheet_id=None):
        """
        Google Maps ve Sheets API'lerini başlatır
        
        Args:
            maps_api_key: Google Maps API anahtarı
            sheets_credentials_path: Service account JSON dosya yolu (optional)
            spreadsheet_id: Google Sheets ID'si (optional)
        """
        # Google Maps client
        self.gmaps = googlemaps.Client(key=maps_api_key)
        
        # Google Sheets setup (optional)
        self.spreadsheet_id = spreadsheet_id
        self.sheets_service = None
        
        if sheets_credentials_path and spreadsheet_id:
            try:
                self.credentials = service_account.Credentials.from_service_account_file(
                    sheets_credentials_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
                logger.info("Google Sheets service initialized")
            except Exception as e:
                logger.warning(f"Google Sheets setup failed: {e}")
                self.sheets_service = None
        
        logger.info("GoogleSheetsRestaurantScraper başlatıldı")
    
    def search_restaurants(self, location, restaurant_type, radius=5000, min_rating=4.5):
        """
        Google Maps'te restoran arar
        
        Args:
            location: Arama yapılacak konum (örn: "üsküdar, istanbul")
            restaurant_type: Restoran türü (örn: "köfteci", "kebapçı")
            radius: Arama yarıçapı (metre)
            min_rating: Minimum puan filtresi (varsayılan: 4.5)
            
        Returns:
            list: Restoran listesi
        """
        restaurants = []
        
        try:
            # Konum koordinatlarını al
            geocode_result = self.gmaps.geocode(f"{location}, istanbul")
            if not geocode_result:
                logger.error(f"Konum bulunamadı: {location}")
                return restaurants
            
            lat_lng = geocode_result[0]['geometry']['location']
            logger.info(f"Geocoding successful for {location}: {lat_lng}")
            
            # Restoran ara
            query = f"{restaurant_type} {location}"
            logger.info(f"{location}'da {restaurant_type} aranıyor...")
            logger.info(f"Search query: {query}, location: {lat_lng}, radius: {radius}")
            
            places_result = self.gmaps.places_nearby(
                location=lat_lng,
                radius=radius,
                keyword=query,
                type='restaurant'
            )
            
            # İlk sayfa sonuçları
            restaurants.extend(self._extract_restaurant_info(places_result.get('results', [])))
            
            # Diğer sayfalar
            while 'next_page_token' in places_result:
                time.sleep(2)  # API rate limit için bekleme
                places_result = self.gmaps.places_nearby(
                    page_token=places_result['next_page_token']
                )
                restaurants.extend(self._extract_restaurant_info(places_result.get('results', [])))
            
            logger.info(f"Toplam {len(restaurants)} restoran bulundu")
            return restaurants
            
        except Exception as e:
            logger.error(f"Arama hatası: {str(e)}")
            return restaurants
    
    def _extract_restaurant_info(self, places, min_rating=4.5):
        """
        Google Places API sonuçlarından restoran bilgilerini çıkarır
        
        Args:
            places: Places API sonuçları
            min_rating: Minimum puan filtresi
            
        Returns:
            list: Restoran bilgileri
        """
        restaurants = []
        
        for place in places:
            # Puan filtresi
            rating = place.get('rating', 0)
            if rating < min_rating:
                continue
                
            # Detaylı bilgi için place details çağrısı
            try:
                place_details = self.gmaps.place(place['place_id'], language='tr')
                details = place_details.get('result', {})
                
                # Çalışma saatlerini al
                opening_hours = self._format_opening_hours(details.get('opening_hours', {}))
                
                restaurant = {
                    'İsim': place.get('name', ''),
                    'Adres': place.get('vicinity', ''),
                    'Puan': rating,
                    'Yorum Sayısı': place.get('user_ratings_total', 0),
                    'Telefon': details.get('formatted_phone_number', 'Bilinmiyor'),
                    'Google Maps URL': f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
                }
                restaurants.append(restaurant)
                
            except Exception as e:
                logger.warning(f"Detay alınamadı: {place.get('name', 'Unknown')} - {str(e)}")
                # Detay alınamazsa temel bilgilerle devam et
                restaurant = {
                    'İsim': place.get('name', ''),
                    'Adres': place.get('vicinity', ''),
                    'Puan': rating,
                    'Yorum Sayısı': place.get('user_ratings_total', 0),
                    'Telefon': 'Bilinmiyor',
                    'Google Maps URL': f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
                    'Tarih': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                restaurants.append(restaurant)
        
        return restaurants
    
    def _format_opening_hours(self, opening_hours):
        """Çalışma saatlerini formatlar"""
        if not opening_hours or 'weekday_text' not in opening_hours:
            return 'Bilinmiyor'
        return ', '.join(opening_hours['weekday_text'])
    
    def create_or_update_sheet(self, sheet_name, data):
        """
        Google Sheets'te sheet oluşturur veya günceller
        
        Args:
            sheet_name: Sheet adı
            data: dict listesi
            
        Returns:
            bool: Başarılı/başarısız
        """
        try:
            # Check if sheets service is available
            if not self.sheets_service:
                logger.warning("Google Sheets service not available")
                return False
                
            # Veri kontrolü
            if not data or not isinstance(data, list):
                return False
            
            # Sheet var mı kontrol et
            sheets_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_exists = any(sheet['properties']['title'] == sheet_name 
                             for sheet in sheets_metadata.get('sheets', []))
            
            # Sheet yoksa oluştur
            if not sheet_exists:
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }]
                }
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=request_body
                ).execute()
                logger.info(f"Yeni sheet oluşturuldu: {sheet_name}")
            
            # Veriyi hazırla - başlık satırı ve veriler
            if data:
                headers = list(data[0].keys())
                values = [headers]
                for row in data:
                    values.append([row.get(header, '') for header in headers])
            else:
                values = []
            
            # Sheet'i temizle ve veriyi yaz
            range_name = f"{sheet_name}!A1"
            
            # Önce sheet'i temizle
            self.sheets_service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:Z"
            ).execute()
            
            # Veriyi yaz
            body = {'values': values}
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"{result.get('updatedCells')} hücre güncellendi")
            
            # Formatla
            self._format_sheet(sheet_name, len(headers) if data else 0, len(values))
            
            return True
            
        except HttpError as e:
            logger.error(f"Google Sheets API hatası: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Sheet güncelleme hatası: {str(e)}")
            return False
    
    def _format_sheet(self, sheet_name, num_columns, num_rows):
        """Sheet'i formatlar"""
        try:
            # Sheet ID'sini al
            sheets_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_id = None
            for sheet in sheets_metadata.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                return
            
            # Format istekleri
            requests = [
                # Başlık satırını kalın yap
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {
                                    "bold": True
                                }
                            }
                        },
                        "fields": "userEnteredFormat.textFormat.bold"
                    }
                },
                # Otomatik sütun genişliği
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": num_columns
                        }
                    }
                }
            ]
            
            body = {'requests': requests}
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            logger.info("Sheet formatlandı")
            
        except Exception as e:
            logger.warning(f"Formatlama hatası (önemsiz): {str(e)}")
    
    def run_search_to_sheets(self, location, restaurant_type, sheet_name):
        """
        Restoran arar ve sonuçları Google Sheets'e yazar
        
        Args:
            location: Arama konumu
            restaurant_type: Restoran türü
            sheet_name: Yazılacak sheet adı
            
        Returns:
            dict: İşlem sonucu
        """
        try:
            # Restoran ara
            restaurants = self.search_restaurants(location, restaurant_type)
            
            if not restaurants:
                return {
                    'success': False,
                    'message': 'Restoran bulunamadı',
                    'count': 0
                }
            
            # Sheet'e yaz
            success = self.create_or_update_sheet(sheet_name, restaurants)
            
            if success:
                return {
                    'success': True,
                    'message': f'{len(restaurants)} restoran bulundu ve kaydedildi',
                    'count': len(restaurants)
                }
            else:
                return {
                    'success': False,
                    'message': 'Sheet güncellenemedi',
                    'count': len(restaurants)
                }
            
        except Exception as e:
            logger.error(f"İşlem hatası: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'count': 0
            }
    
    def batch_search_to_sheets(self, searches):
        """
        Birden fazla arama yapar
        
        Args:
            searches: Arama listesi [{location, restaurant_type, sheet_name}, ...]
            
        Returns:
            list: Sonuçlar
        """
        results = []
        
        for search in searches:
            logger.info(f"İşleniyor: {search['location']} - {search['restaurant_type']}")
            
            result = self.run_search_to_sheets(
                search['location'],
                search['restaurant_type'],
                search['sheet_name']
            )
            
            results.append({
                'location': search['location'],
                'restaurant_type': search['restaurant_type'],
                'sheet_name': search['sheet_name'],
                'result': result
            })
            
            # Rate limit için bekleme
            time.sleep(2)
        
        return results
