import csv
import json
from pathlib import Path

from django.utils.text import slugify

from recipes.models import Ingredient, Tag

csv_path = Path('data/tags.csv').resolve()

with open(csv_path, encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if not row or len(row) < 1:
            continue
        name = row[0].strip()
        slug = row[1].strip() if len(row) > 1 else slugify(name)
        tag, created = Tag.objects.get_or_create(name=name, slug=slug)
        print(f'{"Created" if created else "Exists"}: {tag}')


json_path = Path('data/ingredients.json').resolve()

with open(json_path, encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    ingredient, created = Ingredient.objects.get_or_create(
        name=item['name'],
        measurement_unit=item['measurement_unit']
    )
    if created:
        print(f'Created ingredient: {ingredient}')
    else:
        print(f'Ingredient already exists: {ingredient}')
