from flask import Flask, render_template, request  # type: ignore[import-not-found]
import requests  # type: ignore[import-not-found]

app = Flask(__name__)

GEOCODING_URL = 'https://geocoding-api.open-meteo.com/v1/search'
FORECAST_URL = 'https://api.open-meteo.com/v1/forecast'


@app.route('/', methods=['GET', 'POST'])
def weather_home():
    report = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city', '').strip()

        if not city:
            error = 'Please enter a city name.'
        else:
            try:
                # Phase 1 - Geocoding: city name -> latitude and longitude
                geo_response = requests.get(
                    GEOCODING_URL,
                    params={'name': city, 'count': 1},
                    timeout=10,
                )
                geo_response.raise_for_status()
                geo_data = geo_response.json()

                # When no city matches, the API sends no 'results' key at all
                if 'results' not in geo_data:
                    error = "City '" + city + "' was not found. Check the spelling."
                else:
                    place = geo_data['results'][0]

                    # Phase 2 - Forecast: coordinates -> current weather
                    weather_response = requests.get(
                        FORECAST_URL,
                        params={
                            'latitude': place['latitude'],
                            'longitude': place['longitude'],
                            'current': 'temperature_2m,wind_speed_10m',
                        },
                        timeout=10,
                    )
                    weather_response.raise_for_status()
                    weather_data = weather_response.json()

                    current = weather_data['current']
                    units = weather_data['current_units']

                    # Keep only the values the page needs
                    report = {
                        'city': place['name'],
                        'country': place.get('country', ''),
                        'temperature': current['temperature_2m'],
                        'temperature_unit': units['temperature_2m'],
                        'windspeed': current['wind_speed_10m'],
                        'windspeed_unit': units['wind_speed_10m'],
                        'time': current['time'],
                    }

            except requests.exceptions.RequestException:
                error = 'Could not reach the weather service. Check your internet connection and try again.'
            except (KeyError, ValueError):
                error = 'The weather service sent an unexpected reply. Please try again.'

    return render_template('weather.html', report=report, error=error)


if __name__ == '__main__':
    app.run(debug=True)