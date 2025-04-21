#!/bin/bash

# Make migrations
pip install -r requirements.txt

python3.11 manage.py makemigrations users
python3.11 manage.py makemigrations recipes

# Apply migrations
python3.11 manage.py migrate

# Create superuser (you'll be prompted for credentials)
python3.11 manage.py createsuperuser

# Run the development server
python3.11 manage.py runserver


python3.11 manage.py shell < ./data/load_data.py

