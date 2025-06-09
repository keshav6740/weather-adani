# Django Admin Configuration
# weather/admin.py

from django.contrib import admin
from django.utils.html import format_html
# from django.urls import reverse # Not used in this snippet
from django.utils.safestring import mark_safe
from .models import WeatherSite, WeatherData, WeatherForecast, WeatherAlert


@admin.register(WeatherSite)
class WeatherSiteAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'site_type', 'capacity', 'state', 
        'coordinates', 'is_active', 'latest_weather', 'created_at'
    ]
    list_filter = ['site_type', 'state', 'is_active', 'created_at']
    search_fields = ['name', 'state', 'description']
    readonly_fields = ['created_at', 'updated_at', 'coordinates_map']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'site_type', 'capacity', 'state', 'description')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'coordinates_map')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def coordinates(self, obj):
        """Display coordinates as a formatted string"""
        return f"{obj.latitude}°N, {obj.longitude}°E"
    coordinates.short_description = "Coordinates"
    
    def coordinates_map(self, obj):
        """Display Google Maps link for coordinates"""
        if obj.latitude and obj.longitude:
            maps_url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank" class="btn btn-primary">View on Google Maps</a>',
                maps_url
            )
        return "No coordinates available"
    coordinates_map.short_description = "Map Location"
    
    def latest_weather(self, obj):
        """Display latest weather data for the site"""
        # Relies on WeatherData.Meta.ordering = ['-timestamp']
        latest = obj.weather_data.first()
        if latest:
            return format_html(
                '<span style="color: #0B74B0;">{}°C</span> | <span style="color: #75479C;">{}%</span>',
                latest.temperature if latest.temperature is not None else 'N/A',
                latest.humidity if latest.humidity is not None else 'N/A'
            )
        return format_html('<span style="color: #999;">No data</span>')
    latest_weather.short_description = "Latest Weather (Temp | Humidity)"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('weather_data')


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = [
        'site', 'timestamp', 'temperature', 'humidity', 
        'wind_speed', 'pressure', 'precipitation', 'weather_status'
    ]
    list_filter = ['site', 'timestamp']
    search_fields = ['site__name']
    readonly_fields = ['timestamp', 'weather_summary']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp'] # Explicit ordering here too, good.
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('site', 'timestamp', 'weather_summary')
        }),
        ('Temperature & Humidity', {
            'fields': ('temperature', 'feels_like', 'humidity', 'dew_point')
        }),
        ('Wind', {
            'fields': ('wind_speed', 'wind_direction')
        }),
        ('Atmospheric', {
            'fields': ('pressure', 'surface_pressure', 'precipitation', 'uv_index')
        }),
        ('Visibility & Cloud', {
            'fields': ('cloud_cover', 'visibility')
        })
    )
    
    def weather_status(self, obj):
        """Display weather status with color coding"""
        if obj.temperature is not None:
            if obj.temperature < 10:
                color = "#0dcaf0"  # Cold - Blue
                status = "Cold"
            elif obj.temperature < 25:
                color = "#198754"  # Moderate - Green
                status = "Moderate"
            elif obj.temperature < 35:
                color = "#fd7e14"  # Warm - Orange
                status = "Warm"
            else:
                color = "#dc3545"  # Hot - Red
                status = "Hot"
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, status
            )
        return "N/A"
    weather_status.short_description = "Weather Status"
    
    def weather_summary(self, obj):
        """Display comprehensive weather summary"""
        # This summary relies on fields potentially being None.
        # If a field is None, it will print "None". This is acceptable.
        # The primary check is for obj.temperature to exist to show the summary.
        if obj.temperature is not None: 
            summary = f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; font-family: monospace;">
                <strong style="color: #0B74B0;">Weather Summary for {obj.site.name}</strong><br><br>
                🌡️ <strong>Temperature:</strong> {obj.temperature}°C<br>
                💧 <strong>Humidity:</strong> {obj.humidity if obj.humidity is not None else 'N/A'}%<br>
                💨 <strong>Wind:</strong> {obj.wind_speed if obj.wind_speed is not None else 'N/A'} m/s @ {obj.wind_direction if obj.wind_direction is not None else 'N/A'}°<br>
                ⏱️ <strong>Pressure:</strong> {obj.pressure if obj.pressure is not None else 'N/A'} hPa<br>
                🌧️ <strong>Precipitation:</strong> {obj.precipitation if obj.precipitation is not None else 'N/A'} mm<br>
                ☀️ <strong>UV Index:</strong> {obj.uv_index if obj.uv_index is not None else 'N/A'}<br>
                ☁️ <strong>Cloud Cover:</strong> {obj.cloud_cover if obj.cloud_cover is not None else 'N/A'}%<br>
                👁️ <strong>Visibility:</strong> {obj.visibility if obj.visibility is not None else 'N/A'} km
            </div>
            """
            return mark_safe(summary)
        return "No weather data available"
    weather_summary.short_description = "Weather Summary"


@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    list_display = ['site', 'forecast_time', 'temperature_range', 'precipitation', 'created_at']
    list_filter = ['site', 'forecast_time', 'created_at']
    search_fields = ['site__name']
    date_hierarchy = 'forecast_time'
    ordering = ['forecast_time']
    
    def temperature_range(self, obj):
        """Display temperature range"""
        if obj.temperature_max is not None and obj.temperature_min is not None:
            return f"{obj.temperature_min}°C - {obj.temperature_max}°C"
        return "N/A"
    temperature_range.short_description = "Temperature Range"


@admin.register(WeatherAlert)
class WeatherAlertAdmin(admin.ModelAdmin):
    list_display = ['site', 'alert_type', 'title', 'start_time', 'end_time', 'is_active']
    list_filter = ['alert_type', 'is_active', 'site', 'created_at']
    search_fields = ['title', 'description', 'site__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('site', 'alert_type', 'title', 'description')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('site')


# Custom admin site customization
admin.site.site_header = "Adani Weather Dashboard Administration"
admin.site.site_title = "Adani Weather Admin"
admin.site.index_title = "Weather Dashboard Management"