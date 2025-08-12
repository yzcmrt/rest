import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [foodType, setFoodType] = useState('');
  const [restaurantName, setRestaurantName] = useState('');
  const [minRating, setMinRating] = useState(4.5);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cities, setCities] = useState({});
  const [foodTypes, setFoodTypes] = useState([]);
  const [saveToSheets, setSaveToSheets] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('rating'); // rating, reviewCount, ratingAsc
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [loading2, setLoading2] = useState(false); // Daha fazla yükleme için

  const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? '/api' 
    : 'http://localhost:5001/api';

  // API'den şehirleri al
  useEffect(() => {
    fetchCities();
    fetchFoodTypes();
    loadSearchHistory();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchCities = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/cities`);
      const data = await response.json();
      setCities(data);
    } catch (error) {
      console.error('Şehirler yüklenemedi:', error);
      // Fallback değerler
      setCities({
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
        'İzmir': ['Karşıyaka', 'Bornova', 'Konak', 'Çeşme', 'Alsancak', 'Buca', 'Bayraklı', 'Karabağlar', 'Balçova', 'Narlıdere']
      });
    }
  };

  const fetchFoodTypes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/food-types`);
      const data = await response.json();
      setFoodTypes(data);
    } catch (error) {
      console.error('Yemek türleri yüklenemedi:', error);
      // Fallback değerler
      setFoodTypes([
        'köfteci', 'kebapçı', 'pideci', 'lahmacun', 'dönerci', 'iskender',
        'mantı', 'börekçi', 'gözlemeci', 'çiğ köfte', 'tantuni', 'kokoreç',
        'balık', 'kahvaltı', 'burger', 'pizza', 'sushi', 'italyan',
        'steakhouse', 'tatlıcı', 'dondurmacı', 'kafe', 'meyhane'
      ]);
    }
  };

  const loadSearchHistory = () => {
    const history = localStorage.getItem('searchHistory');
    if (history) {
      setSearchHistory(JSON.parse(history));
    }
  };

  const saveSearchToHistory = (search) => {
    const newHistory = [search, ...searchHistory.filter(h => 
      !(h.city === search.city && h.district === search.district && h.foodType === search.foodType && h.restaurantName === search.restaurantName && h.minRating === search.minRating)
    )].slice(0, 10); // Son 10 arama
    setSearchHistory(newHistory);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));
  };

  const handleSearch = async (loadMore = false) => {
    console.log('🔍 handleSearch çağrıldı!', { loadMore, selectedCity, selectedDistrict, foodType, restaurantName });
    
    if (!selectedCity) {
      alert('Lütfen şehir seçin!');
      return;
    }
    
    if (!selectedDistrict && !foodType && !restaurantName) {
      alert('Lütfen ilçe, yemek türü veya restoran adından en az birini belirtin!');
      return;
    }

    if (loadMore) {
      setLoading2(true);
    } else {
      setLoading(true);
      setCurrentPage(1);
      setResults([]);
    }
    setError('');
    
    try {
      const page = loadMore ? currentPage + 1 : 1;
      const endpoint = saveToSheets ? 'search-and-save' : 'search';
      const url = `${API_BASE_URL}/${endpoint}`;
      const requestBody = {
        city: selectedCity,
        district: selectedDistrict,
        foodType: foodType,
        restaurantName: restaurantName || null,
        minRating: minRating,
        saveToSheets: saveToSheets,
        page: page,
        perPage: 20
      };
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      
      if (data.success) {
        // API'den gelen veriyi düzenle
        const formattedResults = data.data.map(restaurant => ({
          name: restaurant['İsim'] || restaurant.name,
          address: restaurant['Adres'] || restaurant.address,
          rating: restaurant['Puan'] || restaurant.rating,
          reviewCount: restaurant['Yorum Sayısı'] || restaurant.reviewCount,
          phone: restaurant['Telefon'] || restaurant.phone,
          url: restaurant['Google Maps URL'] || restaurant.url
        }));
        
        if (loadMore) {
          setResults(prevResults => [...prevResults, ...formattedResults]);
          setCurrentPage(page);
        } else {
          setResults(formattedResults);
          setCurrentPage(1);
          // Arama geçmişine ekle (sadece yeni arama için)
          saveSearchToHistory({
            city: selectedCity,
            district: selectedDistrict,
            foodType: foodType,
            restaurantName: restaurantName,
            minRating: minRating,
            timestamp: new Date().toISOString(),
            resultCount: data.totalCount || formattedResults.length
          });
        }
        
        setHasMore(data.hasMore || false);
        setTotalCount(data.totalCount || formattedResults.length);
        
        if (saveToSheets && data.sheetName) {
          alert(`Sonuçlar ${data.sheetName} sayfasına kaydedildi!`);
        }
      } else {
        setError(data.error || 'Arama sırasında bir hata oluştu');
        setResults([]);
      }
    } catch (error) {
      console.error('Arama hatası:', error);
      setError('Sunucuya bağlanılamadı. Lütfen daha sonra tekrar deneyin.');
      setResults([]);
    } finally {
      if (loadMore) {
        setLoading2(false);
      } else {
        setLoading(false);
      }
    }
  };

  return (
    <div className="App">
      <div className="container">
        <h1 className="title">🍴 Restoran Bulucu</h1>
        <p className="subtitle">4.5+ puanlı restoranları bulun</p>
        
        <div className="search-container">
          <div className="form-group">
            <label>Şehir</label>
            <select 
              value={selectedCity} 
              onChange={(e) => {
                setSelectedCity(e.target.value);
                setSelectedDistrict('');
              }}
              className="select-input"
            >
              <option value="">Şehir seçin</option>
              {Object.keys(cities).map(city => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>İlçe</label>
            <select 
              value={selectedDistrict} 
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="select-input"
              disabled={!selectedCity}
            >
              <option value="">İlçe seçin</option>
              {selectedCity && cities[selectedCity] && cities[selectedCity].sort().map(district => (
                <option key={district} value={district}>{district}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Yemek Türü</label>
            <select 
              value={foodType} 
              onChange={(e) => setFoodType(e.target.value)}
              className="select-input"
            >
              <option value="">Yemek türü seçin</option>
              {foodTypes.map(type => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Restoran Adı (Opsiyonel)</label>
            <input 
              type="text"
              value={restaurantName} 
              onChange={(e) => setRestaurantName(e.target.value)}
              className="text-input"
              placeholder="Örn: pideci, konya, sultanahmet..."
            />
          </div>

          <div className="form-group">
            <label>Minimum Puan</label>
            <select 
              value={minRating} 
              onChange={(e) => setMinRating(parseFloat(e.target.value))}
              className="select-input"
            >
              <option value="1.0">1.0+ puan</option>
              <option value="1.5">1.5+ puan</option>
              <option value="2.0">2.0+ puan</option>
              <option value="2.5">2.5+ puan</option>
              <option value="3.0">3.0+ puan</option>
              <option value="3.5">3.5+ puan</option>
              <option value="4.0">4.0+ puan</option>
              <option value="4.5">4.5+ puan</option>
              <option value="5.0">5.0 puan</option>
            </select>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input 
                type="checkbox" 
                checked={saveToSheets}
                onChange={(e) => setSaveToSheets(e.target.checked)}
              />
              Google Sheets'e Kaydet
            </label>
          </div>

          <button 
            onClick={() => {
              console.log('🔘 Ara butonu tıklandı!');
              handleSearch();
            }} 
            className="search-button"
            disabled={loading}
          >
            {loading ? 'Aranıyor...' : 'Ara'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {results.length > 0 && (
          <div className="results-container">
            <div className="results-header">
              <h2>Sonuçlar ({results.length}/{totalCount})</h2>
              <div className="sort-buttons">
                <button 
                  className={sortBy === 'rating' ? 'active' : ''}
                  onClick={() => {
                    setSortBy('rating');
                    setResults([...results].sort((a, b) => b.rating - a.rating));
                  }}
                >
                  Puan (Yüksek→Düşük)
                </button>
                <button 
                  className={sortBy === 'ratingAsc' ? 'active' : ''}
                  onClick={() => {
                    setSortBy('ratingAsc');
                    setResults([...results].sort((a, b) => a.rating - b.rating));
                  }}
                >
                  Puan (Düşük→Yüksek)
                </button>
                <button 
                  className={sortBy === 'reviewCount' ? 'active' : ''}
                  onClick={() => {
                    setSortBy('reviewCount');
                    setResults([...results].sort((a, b) => b.reviewCount - a.reviewCount));
                  }}
                >
                  Yorum Sayısına Göre
                </button>
              </div>
            </div>
            <table className="results-table">
              <thead>
                <tr>
                  <th>Restoran Adı</th>
                  <th>Toplam Yorum Sayısı</th>
                  <th>Beğeni Puanı</th>
                  <th>Google Maps URL</th>
                </tr>
              </thead>
              <tbody>
                {results.map((restaurant, index) => (
                  <tr key={index}>
                    <td>{restaurant.name}</td>
                    <td>{restaurant.reviewCount}</td>
                    <td>{restaurant.rating}</td>
                    <td>
                      <a 
                        href={restaurant.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="map-url"
                      >
                        {restaurant.url}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {hasMore && (
              <div className="load-more-container">
                <button 
                  className="load-more-button"
                  onClick={() => handleSearch(true)}
                  disabled={loading2}
                >
                  {loading2 ? 'Yükleniyor...' : 'Daha Fazla Göster'}
                </button>
              </div>
            )}
          </div>
        )}

        {searchHistory.length > 0 && (
          <div className="history-section">
            <button 
              className="history-toggle"
              onClick={() => setShowHistory(!showHistory)}
            >
              {showHistory ? '🔽' : '▶️'} Arama Geçmişi ({searchHistory.length})
            </button>
            {showHistory && (
              <div className="history-list">
                {searchHistory.map((item, index) => (
                  <div key={index} className="history-item" 
                    onClick={() => {
                      setSelectedCity(item.city);
                      setSelectedDistrict(item.district);
                      setFoodType(item.foodType);
                      setRestaurantName(item.restaurantName || '');
                      setMinRating(item.minRating || 4.5);
                    }}
                  >
                    <span>
                      {item.city} - {item.district} - {item.foodType}
                      {item.restaurantName && ` - "${item.restaurantName}"`}
                      {item.minRating && ` - ${item.minRating}+`}
                    </span>
                    <span className="result-count">{item.resultCount} sonuç</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
