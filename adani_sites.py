import os
import json

# Define the Adani power plant sites data
adani_sites_data = { # Renamed to avoid conflict with module name
    "Kamuthi Solar Power Project": {
        "latitude": 9.3476,
        "longitude": 78.3922,
        "capacity": "648 MW",
        "type": "Solar",
        "state": "Tamil Nadu"
    },
    "Bitta Solar Power Plant": {
        "latitude": 23.0470,
        "longitude": 68.8350,
        "capacity": "40 MW",
        "type": "Solar",
        "state": "Gujarat"
    },
    "Bathinda Solar Power Plant": {
        "latitude": 30.2110,
        "longitude": 74.9455,
        "capacity": "100 MW",
        "type": "Solar",
        "state": "Punjab"
    },
    "Chitrakoot Solar Power Plant": {
        "latitude": 25.2000,
        "longitude": 80.9000,
        "capacity": "50 MW",
        "type": "Solar",
        "state": "Uttar Pradesh"
    },
    "Kutch Wind Farm": {
        "latitude": 23.0949,
        "longitude": 69.6126,
        "capacity": "150 MW",
        "type": "Wind",
        "state": "Gujarat"
    },
    "Sadla Wind Farm": {
        "latitude": 23.1374,
        "longitude": 71.8571,
        "capacity": "18 MW",
        "type": "Wind",
        "state": "Gujarat"
    },
    "Khavda Renewable Energy Park": {
        "latitude": 23.7330,
        "longitude": 68.5000,
        "capacity": "30,000 MW (Planned)",
        "type": "Hybrid",
        "state": "Gujarat"
    },
    "Jaisalmer Hybrid Power Plant": {
        "latitude": 26.9157,
        "longitude": 70.9083,
        "capacity": "2,140 MW",
        "type": "Hybrid",
        "state": "Rajasthan"
    }
}

# Save the sites data as JSON for use in Django (e.g., for a data migration or management command)
# Ensure this path is correct relative to where you run the script, or use an absolute path.
output_file_path = 'adani_sites.json' 
with open(output_file_path, 'w') as f:
    json.dump(adani_sites_data, f, indent=2)

print(f"Adani sites data created successfully at {os.path.abspath(output_file_path)}!")
print(f"Total sites: {len(adani_sites_data)}")
for name, data in adani_sites_data.items():
    print(f"- {name}: {data['type']} ({data['capacity']}) in {data['state']}")