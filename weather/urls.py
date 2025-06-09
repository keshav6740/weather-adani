# weather/urls.py
from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('temperature-trends/', views.temperature_trends_view, name='temperature_trends'),
    path('ensemble-forecasts/', views.ensemble_forecast_trends_view, name='ensemble_forecast_trends'),
    path('satellite-imagery/', views.satellite_imagery_view, name='satellite_imagery'),

    # API Endpoints
    path('api/weather/<int:site_id>/current/', views.get_weather_data, name='api_weather_data'),
    path('api/weather/<int:site_id>/forecast-summary/', views.get_forecast_data, name='api_forecast_data'), # For daily summary chart
    
    # Historical data chart endpoint (kept for other uses)
    path('api/chart-data/<int:site_id>/<str:chart_type>/', views.get_chart_data, name='api_chart_data'), 
    
    # New Forecast chart data endpoints for dashboard
    path('api/forecast-chart/hourly/<int:site_id>/<str:chart_type>/', views.get_hourly_forecast_chart_data, name='api_hourly_forecast_chart_data'),
    path('api/forecast-chart/daily-precipitation/<int:site_id>/', views.get_daily_precipitation_forecast_chart_data, name='api_daily_precipitation_forecast_chart_data'),

    path('api/temperature-trend/<int:site_id>/', views.get_temperature_trend_data, name='api_temperature_trend_data'),
    path('api/ensemble-forecast/<int:site_id>/<str:variable_name>/', views.get_ensemble_forecast_trend_data, name='api_ensemble_forecast_trend_data'),
    path('api/wind-rose/<int:site_id>/', views.get_wind_rose_data, name='api_wind_rose'),
    path('api/sites-geojson/', views.get_sites_geojson, name='api_sites_geojson'),
    path('api/update-weather/', views.update_weather_data, name='api_update_weather'),
]