# recipes/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator

User = get_user_model()


class Tag(models.Model):
    """Tag model for recipes."""

    name = models.CharField(
        'Name',
        max_length=200,
        unique=True,
    )
    slug = models.SlugField(
        'Slug',
        max_length=200,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message='Slug contains invalid characters'
            )
        ]
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient model for recipes."""

    name = models.CharField(
        'Name',
        max_length=200,
    )
    measurement_unit = models.CharField(
        'Measurement unit',
        max_length=200,
    )

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Recipe model."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Author',
    )
    name = models.CharField(
        'Name',
        max_length=200,
    )
    image = models.ImageField(
        'Image',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        'Description',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ingredients',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Tags',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Cooking time (minutes)',
        validators=[
            MinValueValidator(
                1, message='Cooking time must be at least 1 minute'
            )
        ]
    )
    pub_date = models.DateTimeField(
        'Publication date',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Through model for Recipe and Ingredient."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Recipe',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        'Amount',
        validators=[
            MinValueValidator(
                1, message='Amount must be at least 1'
            )
        ]
    )

    class Meta:
        verbose_name = 'Recipe ingredient'
        verbose_name_plural = 'Recipe ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.recipe}: {self.ingredient} - {self.amount}'


class Favorite(models.Model):
    """Model for favorite recipes."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='User',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Recipe',
    )

    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} likes {self.recipe}'


class ShoppingCart(models.Model):
    """Model for shopping cart."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='User',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Recipe',
    )

    class Meta:
        verbose_name = 'Shopping cart item'
        verbose_name_plural = 'Shopping cart items'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} added {self.recipe} to shopping cart'
