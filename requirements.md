Django Weather Dashboard Requirements
Project Structure
text
adani_weather_dashboard/
├── manage.py
├── requirements.txt
├── adani_dashboard/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── weather/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── utils.py
    ├── static/
    │   ├── css/
    │   │   └── adani-theme.css
    │   ├── js/
    │   │   ├── charts.js
    │   │   ├── wind-rose.js
    │   │   └── map.js
    │   └── img/
    └── templates/
        └── weather/
            ├── base.html
            ├── dashboard.html
            └── components/
                ├── weather-cards.html
                ├── charts.html
                └── map.html
Dependencies
text
Django==4.2.7
requests==2.31.0
requests-cache==1.1.1
retry-requests==2.0.0
openmeteo-requests==1.2.0
pandas==2.1.4
django-leaflet==0.29.0
plotly==5.17.0
Adani Sites Data
Solar Power Plants
Kamuthi Solar Power Project, Tamil Nadu: 648 MW (9.3476°N, 78.3922°E)

Bitta Solar Power Plant, Gujarat: 40 MW (23.0470°N, 68.8350°E)

Bathinda Solar Power Plant, Punjab: 100 MW (30.2110°N, 74.9455°E)

Chitrakoot Solar Power Plant, Uttar Pradesh: 50 MW (25.2000°N, 80.9000°E)

Wind Power Plants
Kutch Wind Farm, Gujarat: 150 MW (23.0949°N, 69.6126°E)

Sadla Wind Farm, Gujarat: 18 MW (23.1374°N, 71.8571°E)

Hybrid Power Plants
Khavda Renewable Energy Park, Gujarat: 30,000 MW (23.7330°N, 68.5000°E)

Jaisalmer Hybrid Power Plant, Rajasthan: 2,140 MW (26.9157°N, 70.9083°E)

Adani Brand Colors
Primary Blue: #0B74B0

Purple: #75479C

Red: #BD3861

Secondary Blue: #0680A8

Secondary Purple: #5D58A6

Secondary Red: #BB3866

Weather Parameters from Open Meteo API
Current Weather
Temperature (2m)

Humidity

Wind Speed (10m)

Wind Direction

Atmospheric Pressure

Precipitation

UV Index

Forecast Data
Hourly forecasts for 7 days

Daily forecasts for 16 days

Historical data available

Dashboard Features
Left Panel
Weather Cards: Temperature, Humidity, Wind Speed, Pressure, Precipitation, UV Index

Charts Section:

Temperature chart (fixed)

Wind speed chart (fixed)

Precipitation chart (fixed)

Custom chart (user selectable dropdown)

Right Panel
Wind Rose Chart: Interactive wind direction/speed visualization

Daily Weather Summary: Bar chart showing daily trends

Map: Interactive map of India with Adani site markers

Top Filters
Site selection dropdown with preset coordinates

Latitude/Longitude display

Site information (capacity, type, location)