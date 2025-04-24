#!/bin/bash
set -e

# Fake-initial for already existing tables
python3.11 manage.py migrate --fake-initial

# Apply all migrations
python3.11 manage.py migrate

# Collect static files
python3.11 manage.py collectstatic --noinput

# Copy collected static to the right place
cp -r /app/collected_static/. /backend_static/static/

# Ensure the data file is executable (not really necessary for .py, but included as per your command)
chmod +x /app/data/load_data.py

# Load data into the app
python3.11 manage.py shell < /app/data/load_data.py

# Start the Gunicorn server
exec gunicorn --bind 0.0.0.0:8000 foodgram.wsgi
