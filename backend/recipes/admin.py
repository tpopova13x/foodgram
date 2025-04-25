# recipes/admin.py

# recipes/admin.py
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Count

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    """Inline admin for RecipeIngredient model."""

    model = RecipeIngredient
    min_num = 1
    extra = 1
    autocomplete_fields = ("ingredient",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin configuration for Recipe model."""

    list_display = ("id", "name", "author", "favorites_count")
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("tags",)
    inlines = (RecipeIngredientInline,)
    readonly_fields = ("favorites_count",)

    def get_queryset(self, request):
        """Add favorites count to queryset."""
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count("favorited_by"))

    def favorites_count(self, obj):
        """Display number of favorites."""
        return obj.favorited_by.count()

    favorites_count.short_description = "In favorites"

    def save_related(self, request, form, formsets, change):
        """Override save_related to add validation for ingredients."""
        super().save_related(request, form, formsets, change)

        # After saving related objects, check if the recipe has ingredients
        recipe = form.instance
        if not RecipeIngredient.objects.filter(recipe=recipe).exists():
            # If no ingredients exist, raise a validation error
            raise ValidationError(
                "A recipe must have at least one ingredient.")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for Tag model."""

    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin configuration for Ingredient model."""

    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin configuration for Favorite model."""

    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Admin configuration for ShoppingCart model."""

    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
