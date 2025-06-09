# weather/views.py
import logging
from datetime import datetime, timedelta
from django.utils import timezone
import json # For default_ensemble_models_json

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
import numpy as np
import pandas as pd

from .models import WeatherSite, WeatherData, WeatherForecast
from .utils import WeatherAPIClient

logger = logging.getLogger(__name__)

# Constants for Ensemble Forecast View
ENSEMBLE_FORECAST_VARIABLES = [
    ("shortwave_radiation", "Shortwave Radiation (W/m²)"),
    ("wind_speed_80m", "Wind Speed 80m (m/s)"),
    ("wind_speed_100m", "Wind Speed 100m (m/s)"),
]

def get_model_display_name(model_code):
    name = model_code.replace('_seamless', ' Seamless').replace('_ifs025', ' IFS025').replace('_', ' ')
    return name.title()

ENSEMBLE_MODEL_OPTIONS = [("all", "All Ensemble Models")] + \
                         [(code, get_model_display_name(code)) for code in WeatherAPIClient.DEFAULT_ENSEMBLE_MODELS]


def dashboard_view(request):
    """Main dashboard view"""
    sites = WeatherSite.objects.filter(is_active=True).order_by('name')
    selected_site = None

    if not sites.exists():
        messages.warning(request, "No active weather sites found. Please add or activate sites in the admin panel.")
    else:
        selected_site_id_str = request.GET.get('site')
        if selected_site_id_str:
            try:
                selected_site_id = int(selected_site_id_str)
                selected_site = WeatherSite.objects.get(id=selected_site_id, is_active=True)
            except (ValueError, WeatherSite.DoesNotExist):
                messages.warning(request, f"Requested site ID '{selected_site_id_str}' is invalid or site is inactive. Displaying default site.")
                selected_site = sites.first()
        else:
            selected_site = sites.first()

    context = {
        'sites': sites,
        'selected_site': selected_site,
        'adani_colors': getattr(settings, 'ADANI_COLORS', {}),
    }

    return render(request, 'weather/dashboard.html', context)

def temperature_trends_view(request):
    sites = WeatherSite.objects.filter(is_active=True).order_by('name')
    selected_site = None

    if not sites.exists():
        messages.warning(request, "No active weather sites found. Please add or activate sites in the admin panel.")
    else:
        selected_site_id_str = request.GET.get('site')
        if selected_site_id_str:
            try:
                selected_site_id = int(selected_site_id_str)
                selected_site = WeatherSite.objects.get(id=selected_site_id, is_active=True)
            except (ValueError, WeatherSite.DoesNotExist):
                messages.warning(request, f"Requested site ID '{selected_site_id_str}' is invalid or site is inactive. Displaying default site.")
                selected_site = sites.first()
        else:
            selected_site = sites.first()

    days_param = request.GET.get('days', '7')
    current_days_range = 7
    try:
        current_days_range = int(days_param)
        if not (1 <= current_days_range <= 365):
            current_days_range = 7
    except ValueError:
        current_days_range = 7

    context = {
        'sites': sites,
        'selected_site': selected_site,
        'page_title': "Historical Temperature Trends",
        'current_days_range': current_days_range,
        'adani_colors': getattr(settings, 'ADANI_COLORS', {}),
    }
    return render(request, 'weather/temperature_trends.html', context)


def ensemble_forecast_trends_view(request):
    sites = WeatherSite.objects.filter(is_active=True).order_by('name')
    selected_site = None

    if not sites.exists():
        messages.warning(request, "No active weather sites found. Please add or activate sites in the admin panel.")
    else:
        selected_site_id_str = request.GET.get('site')
        if selected_site_id_str:
            try:
                selected_site_id = int(selected_site_id_str)
                selected_site = WeatherSite.objects.get(id=selected_site_id, is_active=True)
            except (ValueError, WeatherSite.DoesNotExist):
                messages.warning(request, f"Requested site ID '{selected_site_id_str}' is invalid or site is inactive. Displaying default site.")
                selected_site = sites.first()
        else:
            selected_site = sites.first()

    current_variable = request.GET.get('variable', ENSEMBLE_FORECAST_VARIABLES[0][0] if ENSEMBLE_FORECAST_VARIABLES else '')

    forecast_days_param = request.GET.get('forecast_days', '7')
    current_forecast_days = 7
    try:
        current_forecast_days = int(forecast_days_param)
        if not (1 <= current_forecast_days <= 16):
            current_forecast_days = 7
    except ValueError:
        current_forecast_days = 7

    current_model_filter = request.GET.get('model_filter', 'all')


    context = {
        'sites': sites,
        'selected_site': selected_site,
        'page_title': "Ensemble Forecast Trends",
        'ensemble_variables': ENSEMBLE_FORECAST_VARIABLES,
        'current_variable': current_variable,
        'current_forecast_days': current_forecast_days,
        'forecast_days_options': list(range(1, 17)),
        'adani_colors': getattr(settings, 'ADANI_COLORS', {}),
        'ensemble_model_options': ENSEMBLE_MODEL_OPTIONS,
        'current_model_filter': current_model_filter,
    }
    return render(request, 'weather/ensemble_forecast_trends.html', context)


@cache_page(5 * 60)
def get_weather_data(request, site_id):
    site = get_object_or_404(WeatherSite, id=site_id, is_active=True)
    cache_key = f"weather_data_current_site_{site_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    try:
        weather_client = WeatherAPIClient()
        api_response = weather_client.get_current_weather(site.latitude, site.longitude)

        if api_response and api_response.get("time"):
            db_data_fields = {
                'temperature': api_response.get('temperature_2m'),
                'humidity': api_response.get('relative_humidity_2m'),
                'wind_speed': api_response.get('wind_speed_10m'),
                'wind_direction': api_response.get('wind_direction_10m'),
                'pressure': api_response.get('surface_pressure'),
                'precipitation': api_response.get('precipitation'),
                'uv_index': api_response.get('uv_index'),
                'cloud_cover': api_response.get('cloud_cover'),
                'feels_like': api_response.get('apparent_temperature'),
                'visibility': api_response.get('visibility')
            }
            for key, value in db_data_fields.items():
                if value is not None:
                    try: db_data_fields[key] = float(value)
                    except (ValueError, TypeError):
                        db_data_fields[key] = None

            WeatherData.objects.create(site=site, **db_data_fields)
            cache.set(cache_key, api_response, 5 * 60)
            return JsonResponse(api_response)
        else:
            logger.warning(f"WeatherAPIClient.get_current_weather returned None or incomplete data for site {site.name} (ID: {site.id}). API Response: {api_response}")
            if isinstance(api_response, dict):
                 return JsonResponse(api_response)
            return JsonResponse({'error': 'Unable to fetch current weather data from external API (client returned invalid data)'}, status=502)
    except Exception as e:
        logger.error(f"CRITICAL ERROR in get_weather_data for site {site.name} (ID: {site.id}): {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Internal server error while fetching current weather data'}, status=500)

@cache_page(10 * 60)
def get_forecast_data(request, site_id):
    site = get_object_or_404(WeatherSite, id=site_id, is_active=True)
    cache_key = f"weather_data_forecast_summary_site_{site_id}"; cached_data = cache.get(cache_key)
    if cached_data: return JsonResponse(cached_data)
    try:
        weather_client = WeatherAPIClient()
        api_forecast_response = weather_client.get_forecast(
            site.latitude, site.longitude,
            daily_params=["temperature_2m_max", "temperature_2m_min", "weather_code"],
            forecast_days=7
        )
        if api_forecast_response and "daily" in api_forecast_response and api_forecast_response["daily"].get("time"):
            cache.set(cache_key, api_forecast_response, 10 * 60)
            return JsonResponse(api_forecast_response)
        else:
            return JsonResponse({'error': 'Unable to fetch forecast summary data from external API or data malformed'}, status=502)
    except Exception as e:
        logger.error(f"Error in get_forecast_data (summary) for site {site.id}: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error while fetching forecast summary data'}, status=500)

def get_chart_data(request, site_id, chart_type):
    site = get_object_or_404(WeatherSite, id=site_id, is_active=True)
    hours = int(request.GET.get('hours', 24))
    start_time = timezone.now() - timedelta(hours=hours)
    field_map = {
        'temperature': 'temperature', 'wind_speed': 'wind_speed', 'precipitation': 'precipitation',
        'pressure': 'pressure', 'humidity': 'humidity', 'cloud_cover': 'cloud_cover',
        'visibility': 'visibility', 'uv_index': 'uv_index', 'feels_like': 'feels_like'
    }
    model_field_name = field_map.get(chart_type)
    if not model_field_name: return JsonResponse({'error': 'Invalid chart type specified'}, status=400)
    weather_data_qs = WeatherData.objects.filter(site=site, timestamp__gte=start_time).order_by('timestamp').values('timestamp', model_field_name)
    labels = [item['timestamp'].isoformat() for item in weather_data_qs]
    dataset_values = [float(item[model_field_name]) if item[model_field_name] is not None else None for item in weather_data_qs]
    chart_configs = {
        'temperature': {'label': 'Temperature (°C)', 'color_key': 'primary_blue'}, 'wind_speed': {'label': 'Wind Speed (m/s)', 'color_key': 'purple'},
        'precipitation': {'label': 'Precipitation (mm)', 'color_key': 'red', 'type': 'bar'}, 'pressure': {'label': 'Pressure (hPa)', 'color_key': 'secondary_blue'},
        'humidity': {'label': 'Humidity (%)', 'color_key': 'secondary_purple'}, 'cloud_cover': {'label': 'Cloud Cover (%)', 'color_key': 'primary_blue'},
        'visibility': {'label': 'Visibility (km)', 'color_key': 'purple'}, 'uv_index': {'label': 'UV Index', 'color_key': 'red'},
        'feels_like': {'label': 'Feels Like (°C)', 'color_key': 'secondary_purple'},
    }
    config = chart_configs.get(chart_type)
    if not config: return JsonResponse({'error': 'Chart configuration error'}, status=500)
    adani_colors = getattr(settings, 'ADANI_COLORS', {}); border_color = adani_colors.get(config['color_key'], '#007bff')
    response_data = {'labels': labels, 'datasets': [{'label': config['label'], 'data': dataset_values, 'borderColor': border_color, 'backgroundColor': border_color + '33', 'fill': True, 'tension': 0.3}], 'type': config.get('type', 'line')}
    return JsonResponse(response_data)

def get_hourly_forecast_chart_data(request, site_id, chart_type):
    site = get_object_or_404(WeatherSite, id=site_id, is_active=True)
    om_param_map = {'temperature': 'temperature_2m', 'wind_speed': 'wind_speed_10m', 'pressure': 'surface_pressure', 'humidity': 'relative_humidity_2m', 'cloud_cover': 'cloud_cover', 'uv_index': 'uv_index', 'feels_like': 'apparent_temperature'}
    open_meteo_param = om_param_map.get(chart_type)
    if not open_meteo_param: return JsonResponse({'error': 'Invalid chart type for hourly forecast'}, status=400)
    weather_client = WeatherAPIClient(); forecast_data = weather_client.get_forecast(site.latitude, site.longitude, hourly_params=[open_meteo_param], forecast_days=7)
    if not forecast_data or "hourly" not in forecast_data or not forecast_data["hourly"].get("time"): return JsonResponse({'error': f'Unable to fetch hourly forecast data for {chart_type}'}, status=502)
    hourly_data = forecast_data["hourly"]; labels = hourly_data.get("time", []); dataset_values = hourly_data.get(open_meteo_param, [])
    chart_configs = {'temperature': {'label': 'Temperature Forecast (°C)', 'color_key': 'primary_blue'},'wind_speed': {'label': 'Wind Speed Forecast (m/s)', 'color_key': 'purple'},'pressure': {'label': 'Pressure Forecast (hPa)', 'color_key': 'secondary_blue'},'humidity': {'label': 'Humidity Forecast (%)', 'color_key': 'secondary_purple'},'cloud_cover': {'label': 'Cloud Cover Forecast (%)', 'color_key': 'primary_blue'},'uv_index': {'label': 'UV Index Forecast', 'color_key': 'red'},'feels_like': {'label': 'Feels Like Forecast (°C)', 'color_key': 'secondary_purple'},}
    config = chart_configs.get(chart_type)
    if not config: return JsonResponse({'error': 'Chart configuration error for forecast'}, status=500)
    adani_colors = getattr(settings, 'ADANI_COLORS', {}); border_color = adani_colors.get(config['color_key'], '#007bff')
    response_data = {'labels': labels, 'datasets': [{'label': config['label'], 'data': dataset_values, 'borderColor': border_color, 'backgroundColor': border_color + '33', 'fill': True, 'tension': 0.3}], 'type': 'line'}
    return JsonResponse(response_data)

def get_daily_precipitation_forecast_chart_data(request, site_id):
    site = get_object_or_404(WeatherSite, id=site_id, is_active=True)
    weather_client = WeatherAPIClient(); forecast_data = weather_client.get_forecast(site.latitude, site.longitude, daily_params=['precipitation_sum'], forecast_days=7)
    if not forecast_data or "daily" not in forecast_data or not forecast_data["daily"].get("time"): return JsonResponse({'error': 'Unable to fetch daily precipitation forecast data'}, status=502)
    daily_data = forecast_data["daily"]; labels = daily_data.get("time", []); dataset_values = daily_data.get('precipitation_sum', [])
    adani_colors = getattr(settings, 'ADANI_COLORS', {}); border_color = adani_colors.get('red', '#BD3861')
    response_data = {'labels': labels, 'datasets': [{'label': 'Daily Precipitation Sum (mm)', 'data': dataset_values, 'borderColor': border_color, 'backgroundColor': border_color + '77', 'fill': False, 'borderWidth': 1}], 'type': 'bar'}
    return JsonResponse(response_data)

# --- ENSEMBLE FORECAST TRENDS (MEAN/MIN/MAX VIEW) ---
def get_ensemble_forecast_trend_data(request, site_id, variable_name):
    try:
        site = get_object_or_404(WeatherSite, id=site_id, is_active=True)
    except Http404:
        return JsonResponse({'error': 'Site not found or inactive'}, status=404)

    if not any(variable_name == var_info[0] for var_info in ENSEMBLE_FORECAST_VARIABLES):
        return JsonResponse({'error': f'Variable {variable_name} not supported'}, status=400)

    forecast_days_str = request.GET.get('forecast_days', '7')
    forecast_days = 7
    try:
        forecast_days = int(forecast_days_str)
        if not (1 <= forecast_days <= 16): forecast_days = 7
    except ValueError: forecast_days = 7

    model_filter_from_request = request.GET.get('model_filter', 'all')
    logger.info(f"Requesting AGGREGATED ensemble data for site {site.id}, var {variable_name}, days {forecast_days}, model_filter: {model_filter_from_request}")

    weather_client = WeatherAPIClient()
    ensemble_api_data = weather_client.get_ensemble_hourly_data(
        latitude=site.latitude, longitude=site.longitude,
        hourly_vars=[variable_name],
        models=WeatherAPIClient.DEFAULT_ENSEMBLE_MODELS, # Always fetch all models for potential aggregation
        forecast_days=forecast_days
    )

    if not ensemble_api_data or "time" not in ensemble_api_data or not ensemble_api_data["time"]:
        logger.error(f"Failed to fetch or parse base ensemble data for site {site.id}, var {variable_name}")
        return JsonResponse({'error': 'No time data or base ensemble data unavailable.'}, status=500)

    labels_utc_iso = ensemble_api_data.get("time", [])
    num_time_steps = len(labels_utc_iso)
    unit = ensemble_api_data.get("hourly_units", {}).get(variable_name, "")
    
    # This will contain all member data for the requested variable_name, e.g., {"icon_seamless_member_0": [...], "gfs_seamless_member_1": [...]}
    all_member_data_for_variable = ensemble_api_data.get("variables", {}).get(variable_name, {})

    if not all_member_data_for_variable:
        logger.warning(f"No member data found for variable '{variable_name}' in ensemble_api_data.variables.")
        return JsonResponse({'error': f'No member data found for variable {variable_name}.'}, status=500)

    output_datasets = []
    model_colors = {
        'icon_seamless': '#2ca02c',  # Green
        'gfs_seamless': '#ff7f0e',   # Orange
        'ecmwf_ifs025': '#1f77b4'    # Blue
    }
    # Determine which models to process based on the filter
    models_to_process = []
    if model_filter_from_request == 'all':
        models_to_process = WeatherAPIClient.DEFAULT_ENSEMBLE_MODELS
    elif model_filter_from_request in WeatherAPIClient.DEFAULT_ENSEMBLE_MODELS:
        models_to_process = [model_filter_from_request]
    
    logger.debug(f"Models to process for aggregation based on filter '{model_filter_from_request}': {models_to_process}")

    for model_code in models_to_process:
        logger.debug(f"Aggregating data for model: {model_code}")
        
        # Collect all data series for the current model_code
        model_specific_member_series = []
        for member_key, member_values in all_member_data_for_variable.items():
            if member_key.startswith(model_code + "_member_"):
                if member_values and len(member_values) == num_time_steps:
                    model_specific_member_series.append(member_values)
                else:
                    logger.warning(f"Member series {member_key} for model {model_code} has mismatched length or is empty. Expected {num_time_steps}, got {len(member_values) if member_values else 0}. Skipping.")
        
        if not model_specific_member_series:
            logger.warning(f"No valid member series found for model {model_code} and variable {variable_name}. Skipping this model.")
            continue
        
        logger.info(f"Found {len(model_specific_member_series)} member series for model {model_code} to aggregate.")

        min_values_for_model = [None] * num_time_steps
        mean_values_for_model = [None] * num_time_steps
        max_values_for_model = [None] * num_time_steps

        for t in range(num_time_steps):
            values_at_t = []
            for series in model_specific_member_series:
                if series[t] is not None: # Ensure np.nanmean etc. handle lists of numbers
                    values_at_t.append(series[t])
            
            if values_at_t: # Only calculate if there's actual data
                min_values_for_model[t] = float(np.nanmin(values_at_t))
                mean_values_for_model[t] = float(np.nanmean(values_at_t))
                max_values_for_model[t] = float(np.nanmax(values_at_t))
            # If values_at_t is empty, they remain None

        base_color_hex = model_colors.get(model_code, '#7f7f7f') # Default to grey
        
        # Create RGBA fill color from hex (e.g., #RRGGBB -> rgba(r,g,b,0.2))
        hex_color_no_hash = base_color_hex.lstrip('#')
        rgb_tuple = tuple(int(hex_color_no_hash[i:i+2], 16) for i in (0, 2, 4))
        fill_rgba_color = f'rgba({rgb_tuple[0]}, {rgb_tuple[1]}, {rgb_tuple[2]}, 0.2)'
        
        model_display_str = get_model_display_name(model_code)

        # Dataset order for Chart.js fill: Max, then Min, then Mean for each model
        # Max dataset (upper boundary of fill)
        output_datasets.append({
            'label': f'_{model_display_str} Range', # Hidden from legend by default due to '_'
            'data': max_values_for_model,
            'borderColor': 'transparent', # No border for the max line itself
            'pointRadius': 0,
            'borderWidth': 0, 
            'fill': '+1',  # Fill to the next dataset in the array (which will be the Min dataset)
            'backgroundColor': fill_rgba_color,
            'order': 1 # Draw fill under the mean line
        })
        # Min dataset (lower boundary of fill)
        output_datasets.append({
            'label': f'_{model_display_str} Min', # Hidden
            'data': min_values_for_model,
            'borderColor': 'transparent',
            'pointRadius': 0,
            'borderWidth': 0,
            'fill': False, # This dataset itself is not filled, it's a boundary
            'order': 2
        })
        # Mean dataset (visible line)
        output_datasets.append({
            'label': model_display_str, # This will show in the legend
            'data': mean_values_for_model,
            'borderColor': base_color_hex, # Solid color for the mean line
            'borderWidth': 2,
            'pointRadius': 0, # Or small radius if preferred
            'fill': False, # The line itself is not filled
            'tension': 0.1,
            'order': 0 # Draw mean line on top
        })
        logger.debug(f"Created aggregated datasets for {model_code}. Mean line label: {model_display_str}")

    if not output_datasets:
         logger.warning(f"No output datasets generated for var: {variable_name}, filter: {model_filter_from_request}")
         # Still send time labels so chart doesn't fully break, but show message from JS
         # Pass empty datasets array to trigger "no data" message in JS

    variable_display_name_from_const = variable_name
    for var_val, var_d_name in ENSEMBLE_FORECAST_VARIABLES:
        if var_val == variable_name:
            variable_display_name_from_const = var_d_name
            break
    
    y_axis_title_str = f"{variable_display_name_from_const} ({unit})" if unit else variable_display_name_from_const

    chart_js_data_response = {
        'labels': labels_utc_iso,
        'datasets': output_datasets,
        'yAxisTitle': y_axis_title_str
    }
    
    logger.info(f"Returning {len(output_datasets)} AGGREGATED datasets for {variable_name} (filter: {model_filter_from_request})")
    return JsonResponse(chart_js_data_response)

def satellite_imagery_view(request):
    """View for displaying satellite imagery slideshows."""
    visible_channels = [
        {"id": "vis1", "name": "Visible 1"},
        {"id": "vis2", "name": "Visible 2"},
        {"id": "vis3", "name": "Visible 3"},
    ]
    infrared_channels = [
        {"id": "ir1", "name": "Infrared 1"},
        {"id": "ir2", "name": "Infrared 2"},
        {"id": "ir3", "name": "Infrared 3"},
        {"id": "ir4", "name": "Infrared 4"},
        {"id": "ir5", "name": "Infrared 5"},
    ]
    context = {
        'page_title': "Satellite Imagery",
        'twenty_four_range': range(24),
        'visible_channels': visible_channels,
        'infrared_channels': infrared_channels,
    }
    return render(request, 'weather/satellite_imagery.html', context)


def get_temperature_trend_data(request, site_id):
    site = get_object_or_404(WeatherSite, id=site_id, is_active=True)
    days = int(request.GET.get('days', '7')); days = max(1, min(365, days))
    start_time = timezone.now() - timedelta(days=days)
    qs = WeatherData.objects.filter(site=site, timestamp__gte=start_time, temperature__isnull=False).order_by('timestamp').values('timestamp', 'temperature')
    labels = [item['timestamp'].isoformat() for item in qs]
    temps = [item['temperature'] for item in qs]
    colors = getattr(settings, 'ADANI_COLORS', {}); border_color = colors.get('primary_blue', '#0B74B0')
    return JsonResponse({'labels': labels, 'datasets': [{'label': f'Temp (°C) - Last {days} Days', 'data': temps, 'borderColor': border_color, 'backgroundColor': border_color + '20', 'fill': True, 'tension': 0.1}]})

def get_wind_rose_data(request, site_id):
    site = get_object_or_404(WeatherSite, id=site_id, is_active=True)
    days = int(request.GET.get('days', 7))
    start_time = timezone.now() - timedelta(days=days)
    qs = WeatherData.objects.filter(site=site, timestamp__gte=start_time, wind_speed__isnull=False, wind_direction__isnull=False).order_by('timestamp').values('timestamp', 'wind_speed', 'wind_direction')
    data_points = [{'direction': i['wind_direction'], 'speed': i['wind_speed'], 'timestamp': i['timestamp'].isoformat()} for i in qs]
    return JsonResponse({'wind_data': data_points})

def get_sites_geojson(request):
    sites_qs = WeatherSite.objects.filter(is_active=True)
    features = []
    for site_obj in sites_qs:
        latest_weather = site_obj.weather_data.order_by('-timestamp').first()
        temp_val = latest_weather.temperature if latest_weather and latest_weather.temperature is not None else None
        popup_html = f"<h6>{site_obj.name}</h6><p><strong>Type:</strong> {site_obj.site_type}</p>"
        popup_html += f'<p><strong>Temp:</strong> {temp_val}°C</p>' if temp_val is not None else '<p>Temp: N/A</p>'
        popup_html += f"<button class='btn btn-sm btn-primary mt-1' onclick='selectSite(\"{site_obj.id}\")'>View Details</button>"
        feature = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [site_obj.longitude, site_obj.latitude]}, 'properties': {'id': site_obj.id, 'name': site_obj.name, 'type': site_obj.site_type, 'capacity': site_obj.capacity, 'state': site_obj.state, 'temperature': temp_val, 'popup_html': popup_html}}
        features.append(feature)
    return JsonResponse({'type': 'FeatureCollection', 'features': features})

@csrf_exempt
def update_weather_data(request):
    if request.method == 'POST':
        try:
            client = WeatherAPIClient(); sites_to_update = WeatherSite.objects.filter(is_active=True)
            updated_count, failed_sites = 0, []
            for site in sites_to_update:
                try:
                    api_response = client.get_current_weather(site.latitude, site.longitude)
                    if api_response and api_response.get("time"):
                        db_data = {k: api_response.get(v) for k, v in {'temperature':'temperature_2m', 'humidity':'relative_humidity_2m', 'wind_speed':'wind_speed_10m', 'wind_direction':'wind_direction_10m', 'pressure':'surface_pressure', 'precipitation':'precipitation', 'uv_index':'uv_index', 'cloud_cover':'cloud_cover', 'feels_like':'apparent_temperature', 'visibility':'visibility'}.items()}
                        for key, val in db_data.items():
                            if val is not None:
                                try: db_data[key] = float(val)
                                except (ValueError, TypeError): db_data[key] = None
                        WeatherData.objects.create(site=site, **db_data)
                        updated_count += 1; cache.delete(f"weather_data_current_site_{site.id}")
                    else:
                        logger.warning(f"No valid API response for site {site.name} during bulk update. API Response: {api_response}")
                        failed_sites.append(site.name)
                except Exception as e_site:
                    logger.error(f"Error updating site {site.name} during bulk update: {e_site}", exc_info=True)
                    failed_sites.append(site.name)
            msg = f'Manual update: {updated_count} of {sites_to_update.count()} sites updated.'
            if failed_sites: msg += f" Failed for: {', '.join(failed_sites)}."
            return JsonResponse({'success': True, 'message': msg, 'updated_count': updated_count, 'failed_count': len(failed_sites)})
        except Exception as e_bulk:
            logger.error(f"CRITICAL ERROR in bulk weather update endpoint: {e_bulk}", exc_info=True)
            return JsonResponse({'success': False, 'error': 'Internal server error during bulk update.'}, status=500)
    return JsonResponse({'error': 'Method not allowed. Please use POST.'}, status=405)