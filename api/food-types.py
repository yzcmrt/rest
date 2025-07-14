from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        food_types = [
            'köfteci', 'kebapçı', 'pideci', 'dondurmacı', 'balık', 
            'kahvaltı', 'burger', 'pizza', 'mantı', 'dönerci',
            'lokanta', 'börekçi', 'tatlıcı', 'kafeterya', 'steakhouse',
            'çiğ köfte', 'tantuni', 'kokoreç', 'midyeci', 'kumru'
        ]
        
        self.wfile.write(json.dumps(food_types).encode())
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
