from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
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
        
        self.wfile.write(json.dumps(food_types).encode())
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
