import googlemaps
import json

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

api_key = config['maps_api_key']
print(f"Testing API key: {api_key[:10]}...{api_key[-4:]}")

# Initialize client
gmaps = googlemaps.Client(key=api_key)

print("\n1. Testing Geocoding API...")
try:
    geocode_result = gmaps.geocode("Üsküdar, Istanbul")
    if geocode_result:
        print("✅ Geocoding API is working!")
        location = geocode_result[0]['geometry']['location']
        print(f"   Location: {location}")
    else:
        print("❌ Geocoding returned no results")
except Exception as e:
    print(f"❌ Geocoding API error: {e}")

print("\n2. Testing Places API (Nearby Search)...")
try:
    # Using Üsküdar coordinates
    places_result = gmaps.places_nearby(
        location={'lat': 41.0266, 'lng': 29.0139},  # Üsküdar coordinates
        radius=1000,
        keyword="köfteci",
        type='restaurant'
    )
    if places_result.get('results'):
        print(f"✅ Places API is working! Found {len(places_result['results'])} places")
        print(f"   First result: {places_result['results'][0].get('name', 'No name')}")
    else:
        print("❌ Places API returned no results")
        print(f"   Status: {places_result.get('status')}")
        if places_result.get('error_message'):
            print(f"   Error: {places_result.get('error_message')}")
except Exception as e:
    print(f"❌ Places API error: {e}")

print("\n3. Testing Places API (Text Search)...")
try:
    places_text = gmaps.places(
        query="köfteci üsküdar istanbul",
        language='tr'
    )
    if places_text.get('results'):
        print(f"✅ Places Text Search is working! Found {len(places_text['results'])} places")
        print(f"   First result: {places_text['results'][0].get('name', 'No name')}")
    else:
        print("❌ Places Text Search returned no results")
        print(f"   Status: {places_text.get('status')}")
except Exception as e:
    print(f"❌ Places Text Search error: {e}")

print("\n4. Checking enabled APIs...")
print("If any of the above failed with 'REQUEST_DENIED', you need to enable that API in Google Cloud Console")
print("\nRequired APIs:")
print("- Places API")
print("- Geocoding API")
print("- Maps JavaScript API (optional for this script)")
