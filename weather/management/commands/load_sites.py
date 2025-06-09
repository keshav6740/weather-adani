import json
import os # Import os to make path joining more robust
from django.conf import settings # To get BASE_DIR
from django.core.management.base import BaseCommand
from weather.models import WeatherSite # Make sure 'weather' is your app_name

class Command(BaseCommand):
    help = 'Loads Adani site data from adani_sites.json into the WeatherSite model'

    def handle(self, *args, **options):
        # Construct the path to adani_sites.json relative to the project's BASE_DIR
        json_file_path = os.path.join(settings.BASE_DIR, 'adani_sites.json') 

        self.stdout.write(f"Attempting to load sites from: {json_file_path}")

        try:
            with open(json_file_path, 'r') as f:
                sites_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"CRITICAL ERROR: '{json_file_path}' not found. Make sure adani_sites.json is in the project root."))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Error: Could not decode JSON from '{json_file_path}'."))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred opening or reading the JSON file: {e}"))
            return


        count_created = 0
        count_updated = 0
        count_skipped = 0

        if not sites_data:
            self.stdout.write(self.style.WARNING("The JSON file is empty or does not contain site data in the expected format."))
            return

        for site_name, data_dict in sites_data.items():
            if not isinstance(data_dict, dict):
                self.stdout.write(self.style.WARNING(f"Skipping entry '{site_name}': data is not a dictionary."))
                count_skipped += 1
                continue
            
            # Map JSON keys to model fields
            defaults = {
                'latitude': data_dict.get('latitude'),
                'longitude': data_dict.get('longitude'),
                'capacity': data_dict.get('capacity'),
                'site_type': data_dict.get('type'), # JSON key is 'type', model is 'site_type'
                'state': data_dict.get('state'),
                'is_active': data_dict.get('is_active', True), # Default to active if not in JSON
                'description': data_dict.get('description', '') 
            }

            # Validate required fields before attempting to create/update
            if defaults['latitude'] is None or defaults['longitude'] is None:
                self.stdout.write(self.style.WARNING(f"Skipping site '{site_name}': missing latitude or longitude."))
                count_skipped += 1
                continue

            try:
                site, created = WeatherSite.objects.update_or_create(
                    name=site_name,
                    defaults=defaults
                )

                if created:
                    count_created += 1
                    self.stdout.write(self.style.SUCCESS(f"Created site: {site.name}"))
                else:
                    count_updated += 1
                    self.stdout.write(f"Updated site: {site.name}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing site '{site_name}': {e}"))
                count_skipped +=1
        
        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully processed sites."))
        self.stdout.write(f"Created: {count_created}, Updated: {count_updated}, Skipped: {count_skipped}")