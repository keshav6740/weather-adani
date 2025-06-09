# Django Models for Weather Dashboard
# weather/models.py

from django.db import models
from django.utils import timezone

class WeatherSite(models.Model):
    """Model to store Adani site information"""
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    capacity = models.CharField(max_length=50) # Kept as CharField as per "no structure change"
    site_type = models.CharField(max_length=20, choices=[
        ('Solar', 'Solar'),
        ('Wind', 'Wind'),
        ('Hybrid', 'Hybrid')
    ])
    state = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.site_type} - {self.capacity})"

class WeatherData(models.Model):
    """Model to store current weather data for each site"""
    site = models.ForeignKey(WeatherSite, on_delete=models.CASCADE, related_name='weather_data')
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Current weather parameters
    temperature = models.FloatField(null=True, blank=True, help_text="Temperature in Celsius")
    humidity = models.FloatField(null=True, blank=True, help_text="Relative humidity in %")
    wind_speed = models.FloatField(null=True, blank=True, help_text="Wind speed in m/s")
    wind_direction = models.FloatField(null=True, blank=True, help_text="Wind direction in degrees")
    pressure = models.FloatField(null=True, blank=True, help_text="Atmospheric pressure in hPa")
    precipitation = models.FloatField(null=True, blank=True, help_text="Precipitation in mm")
    uv_index = models.FloatField(null=True, blank=True, help_text="UV Index")
    cloud_cover = models.FloatField(null=True, blank=True, help_text="Cloud cover in %")
    visibility = models.FloatField(null=True, blank=True, help_text="Visibility in km")
    
    # Additional weather parameters
    feels_like = models.FloatField(null=True, blank=True, help_text="Feels like temperature in Celsius")
    dew_point = models.FloatField(null=True, blank=True, help_text="Dew point in Celsius")
    surface_pressure = models.FloatField(null=True, blank=True, help_text="Surface pressure in hPa")
    
    class Meta:
        ordering = ['-timestamp'] # Important for .first() to get the latest
        indexes = [
            models.Index(fields=['site', '-timestamp']),
        ]
        
    def __str__(self):
        return f"{self.site.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class WeatherForecast(models.Model):
    """Model to store forecast data for each site"""
    site = models.ForeignKey(WeatherSite, on_delete=models.CASCADE, related_name='forecasts')
    forecast_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Forecast parameters
    temperature_max = models.FloatField(null=True, blank=True)
    temperature_min = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    precipitation = models.FloatField(null=True, blank=True)
    precipitation_probability = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['forecast_time']
        unique_together = ['site', 'forecast_time'] # Good for data integrity
        indexes = [
            models.Index(fields=['site', 'forecast_time']),
        ]
        
    def __str__(self):
        return f"{self.site.name} - Forecast for {self.forecast_time.strftime('%Y-%m-%d')}"

class WeatherAlert(models.Model):
    """Model to store weather alerts and warnings"""
    ALERT_TYPES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('SEVERE', 'Severe Weather'),
        ('EXTREME', 'Extreme Weather'),
    ]
    
    site = models.ForeignKey(WeatherSite, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['site', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]
        
    def __str__(self):
        return f"{self.alert_type}: {self.title} - {self.site.name}"