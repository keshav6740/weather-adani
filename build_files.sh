#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Install Python dependencies
pip install -r requirements.txt

# Run Django's collectstatic command
echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Build finished."