#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Collecting static files..."
# The python environment is already active here
python manage.py collectstatic --noinput --clear

echo "Build finished."
