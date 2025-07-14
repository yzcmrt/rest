# Restaurant Finder

Restaurant arama ve listeleme uygulaması. Google Maps API kullanarak belirli bölgelerdeki restoranları arar ve listeler.

## Özellikler

- Şehir ve ilçe bazında restoran arama
- Yemek türüne göre filtreleme
- Restoran detayları (puan, adres, telefon vb.)
- Google Sheets entegrasyonu (opsiyonel)

## Teknolojiler

### Frontend
- React
- Tailwind CSS

### Backend
- Flask (Python)
- Google Maps API
- Google Sheets API

## Kurulum

### Gereksinimler
- Node.js 14+
- Python 3.9+
- Google Maps API Key
- Google Sheets API Credentials (opsiyonel)

### Frontend Kurulumu
```bash
cd frontend
npm install
npm start
```

### Backend Kurulumu
```bash
cd backend
python -m venv venv
source venv/bin/activate  # MacOS/Linux
# veya
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### Yapılandırma

1. `backend/config.json` dosyasını oluşturun:
```json
{
  "maps_api_key": "YOUR_GOOGLE_MAPS_API_KEY",
  "sheets_credentials_path": "credentials.json",
  "spreadsheet_id": "YOUR_SPREADSHEET_ID"
}
```

2. Google Sheets API credentials dosyanızı `backend/credentials.json` olarak kaydedin.

## Deployment

Bu proje Vercel üzerinde monorepo olarak deploy edilmek üzere yapılandırılmıştır.

```bash
vercel
```

## Lisans

MIT
