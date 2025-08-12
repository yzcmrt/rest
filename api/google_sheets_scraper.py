import googlemaps
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from datetime import datetime
import time

# Logging ayarı - Vercel için sadece console'a log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Sadece console'a log, dosyaya yazma
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
    
    def search_restaurants(self, location, restaurant_type, radius=2000, min_rating=4.5, restaurant_name=None):
        """
        Google Maps'te restoran arar
        
        Args:
            location: Arama yapılacak konum (örn: "üsküdar, istanbul")
            restaurant_type: Restoran türü (örn: "köfteci", "kebapçı")
            radius: Arama yarıçapı (metre)
            min_rating: Minimum puan filtresi (varsayılan: 4.5)
            restaurant_name: Opsiyonel restoran adı filtresi
            
        Returns:
            list: Restoran listesi
        """
        restaurants = []
        
        try:
            # İlçe ve şehir bilgilerini ayır
            location_parts = location.split(',')
            district = location_parts[0].strip() if location_parts else location
            
            # Text search kullan - daha spesifik sonuçlar için
            if restaurant_name and restaurant_type != "restaurant":
                # Hem restoran adı hem yemek türü belirtilmişse
                query = f"{restaurant_name} {restaurant_type} in {location}"
            elif restaurant_name:
                # Sadece restoran adı belirtilmişse
                query = f"{restaurant_name} in {location}"
            else:
                # Sadece yemek türü belirtilmişse
                query = f"{restaurant_type} in {location}"
            
            logger.info(f"{location}'da {restaurant_type} aranıyor...")
            if restaurant_name:
                logger.info(f"Restoran adı filtresi: {restaurant_name}")
            logger.info(f"Search query: {query}")
            
            # Text search ile ara - pagination ile tüm sonuçları al
            all_places = []
            next_page_token = None
            max_pages = 3  # Maksimum 3 sayfa (60 sonuç)
            current_page = 0
            
            while current_page < max_pages:
                if current_page == 0:
                    # İlk sayfa
                    places_result = self.gmaps.places(
                        query=query,
                        type='restaurant',
                        language='tr'
                    )
                else:
                    # Sonraki sayfalar için next_page_token gerekli
                    if not next_page_token:
                        break
                    
                    # Token kullanmadan önce kısa bir bekleme (Google API requirement)
                    import time
                    time.sleep(2)
                    
                    places_result = self.gmaps.places(
                        query=query,
                        type='restaurant',
                        language='tr',
                        page_token=next_page_token
                    )
                
                current_results = places_result.get('results', [])
                all_places.extend(current_results)
                
                next_page_token = places_result.get('next_page_token')
                current_page += 1
                
                logger.info(f"Sayfa {current_page}: {len(current_results)} sonuç, toplam: {len(all_places)}")
                
                # Eğer next_page_token yoksa dur
                if not next_page_token:
                    break
            
            logger.info(f"Toplam Google API sonucu: {len(all_places)}")
            
            # Sonuçları filtrele - sadece belirtilen ilçedeki restoranları al
            filtered_results = []
            seen_places = set()  # Duplicate kontrolü için
            
            for place in all_places:
                # Adres kontrolü
                address = place.get('formatted_address', '').lower()
                place_name = place.get('name', '').lower()
                place_id = place.get('place_id')
                
                # Duplicate kontrolü - place_id ile
                if place_id in seen_places:
                    continue
                
                # İlçe kontrolü (sadece district belirtilmişse)
                if len(location_parts) > 1 and district.lower() not in address:
                    continue
                
                # Restoran adı filtresi (eğer belirtilmişse)
                if restaurant_name and restaurant_name.lower() not in place_name:
                    continue
                
                seen_places.add(place_id)
                filtered_results.append(place)
            
            # Filtrelenmiş sonuçları işle
            restaurants.extend(self._extract_restaurant_info(filtered_results))
            
            # Eğer yeterli sonuç yoksa, nearby search ile destekle
            if len(restaurants) < 30:
                # Geocode yap
                geocode_result = self.gmaps.geocode(f"{location}, Türkiye")
                if geocode_result:
                    lat_lng = geocode_result[0]['geometry']['location']
                    
                    # Nearby search - daha küçük yarıçap ile
                    nearby_result = self.gmaps.places_nearby(
                        location=lat_lng,
                        radius=radius,
                        keyword=restaurant_type,
                        type='restaurant'
                    )
                    
                    # Nearby sonuçları da filtrele
                    for place in nearby_result.get('results', []):
                        address = place.get('vicinity', '').lower()
                        place_name = place.get('name', '').lower()
                        place_id = place.get('place_id')
                        
                        # Duplicate kontrolü
                        if place_id in seen_places:
                            continue
                        
                        # İlçe kontrolü (sadece district belirtilmişse) - ESNEK YAKLAŞIM
                        if len(location_parts) > 1:
                            address_normalized = self._normalize_turkish_text(address)
                            district_normalized = self._normalize_turkish_text(district)
                            
                            # Birden fazla kontrol yöntemi - DAHA ESNEK
                            district_found = False
                            
                            # 1. Tam isim kontrolü
                            if district_normalized in address_normalized:
                                district_found = True
                            
                            # 2. Yaygın kısaltmalar kontrolü
                            district_variations = self._get_district_variations(district_normalized)
                            for variation in district_variations:
                                if variation in address_normalized:
                                    district_found = True
                                    break
                            
                            # 3. İstanbul geneli kontrolü - YENI EKLEME
                            if not district_found and 'istanbul' in address_normalized:
                                # Google bazen sadece "İstanbul" yazıyor, ilçe belirtmiyor
                                # Bu durumda koordinat kontrolü yapalım
                                lat = place.get('geometry', {}).get('location', {}).get('lat')
                                lng = place.get('geometry', {}).get('location', {}).get('lng')
                                
                                if lat and lng:
                                    # İstanbul sınırları içindeyse kabul et
                                    if self._is_location_in_bounds(lat, lng, 'İstanbul', district):
                                        district_found = True
                                        logger.debug(f"Koordinat bazlı eşleşme: {district} - {lat},{lng}")
                            
                            # 4. ESNEK YAKLAŞIM: Çok katı olmayalım
                            if not district_found:
                                # Eğer address'te hiçbir ilçe bilgisi yoksa ve İstanbul içindeyse
                                # nearby search results olabilir, kabul edelim
                                if 'istanbul' in address_normalized and not any(
                                    other_district in address_normalized for other_district in 
                                    ['kadikoy', 'besiktas', 'sisli', 'fatih', 'beyoglu', 'uskudar', 
                                     'bagcilar', 'zeytinburnu', 'bakirkoy', 'maltepe']
                                ):
                                    district_found = True
                                    logger.debug(f"Esnek eşleşme (İstanbul genel): {address}")
                                else:
                                    logger.debug(f"İlçe eşleşmedi: {district} != {address}")
                                    continue
                            else:
                                logger.debug(f"İlçe eşleşti: {district} = {address}")
                        
                        # Restoran adı filtresi (eğer belirtilmişse)
                        if restaurant_name and restaurant_name.lower() not in place_name:
                            continue
                        
                        seen_places.add(place_id)
                        filtered_results.append(place)
                    
                    # Yeni sonuçları işle
                    new_restaurants = self._extract_restaurant_info([p for p in filtered_results if p.get('place_id') not in [r.get('place_id') for r in restaurants]])
                    restaurants.extend(new_restaurants)
            
            # Puana göre sırala (yüksekten düşüğe)
            restaurants.sort(key=lambda x: x['Puan'], reverse=True)
            
            logger.info(f"Toplam {len(restaurants)} restoran bulundu ({district} içinde)")
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
                    'place_id': place.get('place_id')
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
                    'place_id': place.get('place_id'),
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
    
    def run_search_to_sheets(self, location, restaurant_type, sheet_name, min_rating=4.5, restaurant_name=None):
        """
        Restoran arar ve sonuçları Google Sheets'e yazar
        
        Args:
            location: Arama konumu
            restaurant_type: Restoran türü
            sheet_name: Yazılacak sheet adı
            min_rating: Minimum puan filtresi
            restaurant_name: Opsiyonel restoran adı filtresi
            
        Returns:
            dict: İşlem sonucu
        """
        try:
            # Restoran ara
            restaurants = self.search_restaurants(location, restaurant_type, min_rating=min_rating, restaurant_name=restaurant_name)
            
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
    
    def _normalize_turkish_text(self, text):
        """Türkçe karakterleri normalize eder ve küçük harfe çevirir"""
        if not text:
            return ""
        
        # Türkçe karakter dönüşümü
        replacements = {
            'ı': 'i', 'İ': 'i', 'ş': 's', 'Ş': 's', 'ğ': 'g', 'Ğ': 'g',
            'ü': 'u', 'Ü': 'u', 'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
        }
        
        normalized = text.lower()
        for tr_char, en_char in replacements.items():
            normalized = normalized.replace(tr_char, en_char)
        
        return normalized
    
    def _get_district_variations(self, district):
        """İlçe isimlerinin yaygın varyasyonlarını döner"""
        variations = [district]
        
        # İstanbul ilçe varyasyonları
        district_variations = {
            'kadikoy': ['kadikoy', 'kadiköy', 'kadıkoy', 'kadıköy'],
            'besiktas': ['besiktas', 'beşiktaş', 'besıktas', 'besıktaş'],
            'sisli': ['sisli', 'şişli'],
            'beyoglu': ['beyoglu', 'beyoğlu'],
            'uskudar': ['uskudar', 'üsküdar'],
            'fatih': ['fatih', 'fatıh'],
            'bakirkoy': ['bakirkoy', 'bakırköy'],
            'maltepe': ['maltepe'],
            'pendik': ['pendik'],
            'tuzla': ['tuzla'],
            'kartal': ['kartal'],
            'atasehir': ['atasehir', 'ataşehir'],
            'umraniye': ['umraniye', 'ümraniye'],
            'cekmekoy': ['cekmekoy', 'çekmeköy'],
            'sancaktepe': ['sancaktepe'],
            'sultanbeyli': ['sultanbeyli'],
            'kucukcekmece': ['kucukcekmece', 'küçükçekmece'],
            'buyukcekmece': ['buyukcekmece', 'büyükçekmece'],
            'avcilar': ['avcilar', 'avcılar'],
            'bagcilar': ['bagcilar', 'bağcılar'],
            'bahcelievler': ['bahcelievler', 'bahçelievler'],
            'esenler': ['esenler'],
            'gaziosmanpasa': ['gaziosmanpasa', 'gaziosmanpaşa'],
            'gungoren': ['gungoren', 'güngören'],
            'sultangazi': ['sultangazi'],
            'eyup': ['eyup', 'eyüp', 'eyupsultan', 'eyüpsultan'],
            'arnavutkoy': ['arnavutkoy', 'arnavutköy'],
            'basaksehir': ['basaksehir', 'başakşehir'],
            'beylikduzu': ['beylikduzu', 'beylikdüzü'],
            'catalca': ['catalca', 'çatalca'],
            'silivri': ['silivri']
        }
        
        # İlgili varyasyonları bul
        for key, vars_list in district_variations.items():
            if district in vars_list:
                variations.extend(vars_list)
                break
        
        return list(set(variations))  # Tekrarları kaldır
    
    def _is_location_in_bounds(self, lat, lng, city, district=None):
        """Verilen koordinatın belirtilen şehir/ilçe sınırları içinde olup olmadığını kontrol eder"""
        try:
            # İstanbul için genel sınırlar
            if city.lower() in ['istanbul', 'İstanbul']:
                istanbul_bounds = {
                    'north': 41.34, 'south': 40.80,
                    'east': 29.70, 'west': 27.80
                }
                
                if not (istanbul_bounds['south'] <= lat <= istanbul_bounds['north'] and
                        istanbul_bounds['west'] <= lng <= istanbul_bounds['east']):
                    return False
                
                # İlçe bazlı detaylı kontrol (sadece bazı büyük ilçeler için)
                if district:
                    district_bounds = self._get_district_bounds(district.lower())
                    if district_bounds:
                        return (district_bounds['south'] <= lat <= district_bounds['north'] and
                                district_bounds['west'] <= lng <= district_bounds['east'])
            
            return True  # Diğer şehirler için şimdilik true
            
        except Exception as e:
            logger.error(f"Lokasyon sınır kontrolü hatası: {str(e)}")
            return True  # Hata durumunda filtreleme yapma
    
    def _get_district_bounds(self, district):
        """İlçe sınırlarını döner (yaklaşık)"""
        district_bounds = {
            'kadikoy': {'north': 40.99, 'south': 40.94, 'east': 29.09, 'west': 29.02},
            'besiktas': {'north': 41.08, 'south': 41.03, 'east': 29.02, 'west': 28.98},
            'sisli': {'north': 41.06, 'south': 41.04, 'east': 28.99, 'west': 28.96},
            'fatih': {'north': 41.02, 'south': 40.99, 'east': 28.98, 'west': 28.93},
            'uskudar': {'north': 41.04, 'south': 40.98, 'east': 29.06, 'west': 29.01},
            'beyoglu': {'north': 41.04, 'south': 41.01, 'east': 28.99, 'west': 28.95},
            'maltepe': {'north': 40.96, 'south': 40.92, 'east': 29.15, 'west': 29.10},
            'pendik': {'north': 40.91, 'south': 40.86, 'east': 29.26, 'west': 29.21},
            'kartal': {'north': 40.91, 'south': 40.87, 'east': 29.21, 'west': 29.16},
            'tuzla': {'north': 40.87, 'south': 40.82, 'east': 29.32, 'west': 29.27}
        }
        
        # Normalize edilmiş district name ile karşılaştır
        district_normalized = self._normalize_turkish_text(district)
        return district_bounds.get(district_normalized)
