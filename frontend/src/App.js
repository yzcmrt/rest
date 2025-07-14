import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [foodType, setFoodType] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cities, setCities] = useState({});
  const [foodTypes, setFoodTypes] = useState([]);
  const [saveToSheets, setSaveToSheets] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('rating'); // rating, reviewCount

  const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? '/api' 
    : 'http://localhost:5000/api';

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
        'İstanbul': ['Üsküdar', 'Kadıköy', 'Beşiktaş', 'Sarıyer', 'Şişli'],
        'Ankara': ['Çankaya', 'Keçiören', 'Mamak'],
        'İzmir': ['Karşıyaka', 'Bornova', 'Konak']
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
      setFoodTypes(['köfteci', 'kebapçı', 'pideci', 'dondurmacı', 'balık']);
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
      !(h.city === search.city && h.district === search.district && h.foodType === search.foodType)
    )].slice(0, 10); // Son 10 arama
    setSearchHistory(newHistory);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));
  };

  const handleSearch = async () => {
    if (!selectedCity || !selectedDistrict || !foodType) {
      alert('Lütfen tüm alanları doldurun!');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const endpoint = saveToSheets ? 'search-and-save' : 'search';
      const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          city: selectedCity,
          district: selectedDistrict,
          foodType: foodType,
          saveToSheets: saveToSheets
        })
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
        
        setResults(formattedResults);
        
        // Arama geçmişine ekle
        saveSearchToHistory({
          city: selectedCity,
          district: selectedDistrict,
          foodType: foodType,
          timestamp: new Date().toISOString(),
          resultCount: formattedResults.length
        });
        
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
      setLoading(false);
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
              {selectedCity && cities[selectedCity].map(district => (
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
            onClick={handleSearch} 
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
              <h2>Sonuçlar ({results.length})</h2>
              <div className="sort-buttons">
                <button 
                  className={sortBy === 'rating' ? 'active' : ''}
                  onClick={() => {
                    setSortBy('rating');
                    setResults([...results].sort((a, b) => b.rating - a.rating));
                  }}
                >
                  Puana Göre
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
            {results.map((restaurant, index) => (
              <div key={index} className="result-card">
                <div className="result-header">
                  <h3>{restaurant.name}</h3>
                  <div className="rating">
                    ⭐ {restaurant.rating} ({restaurant.reviewCount} yorum)
                  </div>
                </div>
                <p className="address">📍 {restaurant.address}</p>
                <p className="phone">📞 {restaurant.phone}</p>
                <a 
                  href={restaurant.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="map-link"
                >
                  Google Maps'te Gör →
                </a>
              </div>
            ))}
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
                    }}
                  >
                    <span>{item.city} - {item.district} - {item.foodType}</span>
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
