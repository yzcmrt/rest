from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
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
        
        self.wfile.write(json.dumps(cities).encode())
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
