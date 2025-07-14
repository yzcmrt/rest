# Vercel Deployment Kılavuzu

Bu proje Vercel'e deploy edilmek üzere yapılandırılmıştır.

## Öngereksinimler

1. Vercel hesabı (https://vercel.com)
2. Google Maps API Key
3. Google Sheets API Credentials (opsiyonel)
4. Google Sheets Spreadsheet ID (opsiyonel)

## Deployment Adımları

### 1. Environment Variables Ayarlama

Vercel dashboard'da projenize gidin ve Settings > Environment Variables'a tıklayın. Aşağıdaki değişkenleri ekleyin:

- `MAPS_API_KEY`: Google Maps API anahtarınız
- `SHEETS_CREDENTIALS`: Google Sheets service account JSON'ınızın içeriği (tek satır string olarak)
- `SPREADSHEET_ID`: Google Sheets ID'niz

### 2. Vercel CLI ile Deploy

```bash
# Vercel CLI kurulumu
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

### 3. GitHub Entegrasyonu

1. Vercel dashboard'da "Import Project" tıklayın
2. GitHub repo'nuzu seçin: https://github.com/yzcmrt/rest
3. Framework Preset: Other
4. Build Settings otomatik algılanacak
5. Environment variables ekleyin
6. Deploy!

## Önemli Notlar

### API Limitleri
- Vercel Functions max 10 saniye timeout'a sahiptir
- Google Maps API günlük limitlerinizi kontrol edin
- Rate limiting için dikkatli olun

### CORS Ayarları
- Frontend ve backend aynı domain'de olduğu için CORS sorunu yaşanmaz
- External API çağrıları için CORS header'ları zaten eklenmiş durumda

### Debug
Eğer deployment'ta sorun yaşarsanız:
1. Vercel Functions loglarını kontrol edin
2. Environment variable'ların doğru set edildiğinden emin olun
3. `vercel logs` komutu ile detaylı log görüntüleyin

### Test Etme
Deployment sonrası:
1. `/api/health` endpoint'ini test edin
2. Frontend'in yüklendiğini kontrol edin
3. Bir arama yaparak API'nin çalıştığını doğrulayın
