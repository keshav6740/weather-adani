# weather/forms.py

from django import forms
from datetime import datetime, timedelta

# Adani Sites Choices
ADANI_SITE_CHOICES = [
    ('', 'Select Adani Site'),
    ('kamuthi_solar', 'Kamuthi Solar Power Project, Tamil Nadu (648 MW)'),
    ('bitta_solar', 'Bitta Solar Power Plant, Gujarat (40 MW)'),
    ('bathinda_solar', 'Bathinda Solar Power Plant, Punjab (100 MW)'),
    ('chitrakoot_solar', 'Chitrakoot Solar Power Plant, Uttar Pradesh (50 MW)'),
    ('kutch_wind', 'Kutch (Adani) VI Wind Farm, Gujarat (150 MW)'),
    ('sadla_wind', 'Sadla Wind Farm, Gujarat (18 MW)'),
    ('khavda_hybrid', 'Khavda Renewable Energy Park, Gujarat (30,000 MW)'),
    ('jaisalmer_hybrid', 'Jaisalmer Hybrid Power Plant, Rajasthan (2,140 MW)'),
]

class WeatherFilterForm(forms.Form):
    site = forms.ChoiceField(
        choices=ADANI_SITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'site-selector'
        })
    )
    latitude = forms.FloatField(
        initial=52.52,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter latitude',
            'step': 'any',
            'id': 'latitude-input'
        })
    )
    longitude = forms.FloatField(
        initial=13.41,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter longitude',
            'step': 'any',
            'id': 'longitude-input'
        })
    )
    start_date = forms.DateField(
        required=False,
        initial=datetime.now().date(),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        initial=datetime.now().date() + timedelta(days=7),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )