# İstanbul İlçeleri Güncelleme Dokümantasyonu

## Yapılan Değişiklikler

### 1. İstanbul'un Tüm İlçeleri Eklendi
`api/cities.py` dosyasında İstanbul için 39 ilçenin tamamı eklenmiştir:

- Adalar
- Arnavutköy
- Ataşehir
- Avcılar
- Bağcılar
- Bahçelievler
- Bakırköy
- Başakşehir
- Bayrampaşa
- Beşiktaş
- Beykoz
- Beylikdüzü
- Beyoğlu
- Büyükçekmece
- Çatalca
- Çekmeköy
- Esenler
- Esenyurt
- Eyüpsultan
- Fatih
- Gaziosmanpaşa
- Güngören
- Kadıköy
- Kağıthane
- Kartal
- Küçükçekmece
- Maltepe
- Pendik
- Sancaktepe
- Sarıyer
- Silivri
- Sultanbeyli
- Sultangazi
- Şile
- Şişli
- Tuzla
- Ümraniye
- Üsküdar
- Zeytinburnu

### 2. API Özellikleri

#### Minimum Puan Filtresi
`api/google_sheets_scraper.py` dosyasında varsayılan olarak **4.5 ve üzeri** puanlı restoranlar filtrelenmektedir:

```python
def search_restaurants(self, location, restaurant_type, radius=2000, min_rating=4.5):
```

#### İlçe Bazlı Filtreleme
Sistem otomatik olarak seçilen ilçedeki restoranları filtrelemektedir. Adres kontrolü yapılarak sadece belirtilen ilçedeki restoranlar listelenir.

### 3. Frontend Entegrasyonu

Frontend (`frontend/src/App.js`) otomatik olarak:
- `/api/cities` endpoint'inden şehir ve ilçe listesini çeker
- Dropdown menüde İstanbul seçildiğinde tüm 39 ilçe gösterilir
- Seçilen ilçe ve yemek türüne göre arama yapar

### 4. Kullanım

1. Frontend'i açın
2. Şehir dropdown'ından "İstanbul" seçin
3. İlçe dropdown'ından istediğiniz ilçeyi seçin (39 ilçenin tamamı listelenecektir)
4. Yemek türünü seçin
5. "Ara" butonuna tıklayın

Sistem otomatik olarak seçilen ilçede 4.5 puan ve üzerindeki restoranları listeleyecektir.

### 5. API Endpoints

- **GET /api/cities**: Tüm şehir ve ilçeleri döner
- **GET /api/food-types**: Desteklenen yemek türlerini döner
- **POST /api/search**: Restoran araması yapar
  - Body: `{city, district, foodType}`
  - Response: 4.5+ puanlı restoranların listesi

### 6. Deployment Notları

Proje Vercel'de deploy edilmiştir. Environment variables olarak:
- `MAPS_API_KEY`: Google Maps API anahtarı
- `SHEETS_CREDENTIALS`: Google Sheets credentials (opsiyonel)
- `SPREADSHEET_ID`: Google Sheets ID (opsiyonel)

ayarlanması gerekmektedir.
