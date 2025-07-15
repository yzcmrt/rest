from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Handle CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
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
        
        response = json.dumps(cities)
        self.wfile.write(response.encode())
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
