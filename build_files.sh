#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- FIX IS HERE ---
# Use the specific versioned pip that matches your vercel.json runtime
echo "Installing dependencies..."

echo "Collecting static files..."
python3.9 manage.py collectstatic --noinput --clear

echo "Build finished."
