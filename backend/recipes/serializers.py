# recipes/serializers.py
from django.core.validators import MinValueValidator
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from users.serializers import CustomUserSerializer

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient model."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for RecipeIngredient model."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model."""

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source="recipe_ingredients"
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_image(self, obj):
        """Return full URL for image."""
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""  # Return empty string if no image

    def get_is_favorited(self, obj):
        """Check if recipe is in user's favorites."""
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Check if recipe is in user's shopping cart."""
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj).exists()


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=[MinValueValidator(1, message="Amount must be at least 1")]
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")

    def to_representation(self, instance):
        # Add debug logging here
        print(f"to_representation called with instance type: {type(instance)}")
        print(f"instance attributes: {dir(instance)}")
        return super().to_representation(instance)

    def to_internal_value(self, data):
        # Add debug logging here
        print(f"to_internal_value called with data type: {type(data)}")
        print(f"data content: {data}")
        return super().to_internal_value(data)

    def validate_amount(self, value):
        """Double check validation for amount field."""
        if value < 1:
            raise serializers.ValidationError("Amount must be at least 1")
        return value


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating recipes."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientWriteSerializer(
        many=True, write_only=True, required=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time")

    def validate(self, data):
        """Validate that required fields"""
        """are present for both create and update operations."""
        errors = {}

        if self.instance:
            if "ingredients" not in data:
                errors["ingredients"] = \
                    "Ingredients are required when updating a recipe"

            if "tags" not in data:
                errors["tags"] = "Tags are required when updating a recipe"

        elif "image" not in data:
            errors["image"] = "Image is required when creating a recipe"

        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(data)

    def validate_ingredients(self, value):
        """Validate ingredients."""
        if not value:
            raise serializers.ValidationError(
                "You need to add at least one ingredient")

        ingredient_ids = [item["id"] for item in value]

        # Check that all ingredients exist in the database
        existing_ids = Ingredient.objects.filter(
            id__in=ingredient_ids).values_list(
            "id", flat=True)
        missing_ids = set(ingredient_ids) - set(existing_ids)
        if missing_ids:
            raise serializers.ValidationError(
                f"Ingredients with IDs {missing_ids} do not exist"
            )

        # Check for duplicate ingredients
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ingredients must be unique")

        for item in value:
            if item["amount"] < 1:
                raise serializers.ValidationError("Amount must be at least 1")
        return value

    def validate_tags(self, value):
        """Validate tags."""
        if not value:
            raise serializers.ValidationError(
                "You need to add at least one tag")

        if len(value) != len(set(value)):
            raise serializers.ValidationError("Tags must be unique")

        return value

    def validate_cooking_time(self, value):
        """Validate cooking time."""
        if value < 1:
            raise serializers.ValidationError(
                "Cooking time must be at least 1 minute")
        return value

    def to_representation(self, instance):
        """Convert instance to proper output format."""
        return RecipeSerializer(instance, context=self.context).data

    def create_ingredients(self, recipe, ingredients_data):
        """Create ingredient objects for the recipe."""
        recipe_ingredients = []
        print(ingredients_data)
        for item in ingredients_data:
            ingredient_id = item["id"]
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient, amount=item["amount"]
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        """Create a new recipe with ingredients and tags."""
        tags = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update an existing recipe with ingredients and tags."""
        tags = validated_data.pop("tags", None)
        ingredients_data = validated_data.pop("ingredients", None)

        for attr, value in validated_data.items():
            if attr == 'image' and value:
                setattr(instance, attr, value)
            elif attr != 'image':
                setattr(instance, attr, value)

        instance.save()

        if tags is not None:
            instance.tags.clear()
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ingredients_data)

        return instance


class RecipeShortSerializer(serializers.ModelSerializer):
    """Serializer for simplified recipe representation in subscriptions."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        """Return full URL for image as a string."""
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""  # Return empty string if no image


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding a recipe to favorites."""

    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=("user", "recipe"),
                message="Recipe is already in favorites"
            )
        ]


class FavoriteDeleteSerializer(serializers.Serializer):
    """Serializer for removing a recipe from favorites."""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Recipe is not in favorites.")

        return data

    def delete(self):
        user = self.validated_data['user']
        recipe = self.validated_data['recipe']
        Favorite.objects.filter(user=user, recipe=recipe).delete()


class ShoppingCartCreateSerializer(serializers.Serializer):
    """Serializer for adding a recipe to the shopping cart."""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Recipe is already in shopping cart.")

        return data

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)


class ShoppingCartDeleteSerializer(serializers.Serializer):
    """Serializer for removing a recipe from the shopping cart."""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if not ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                "Recipe is not in shopping cart.")

        return data

    def delete(self):
        user = self.validated_data['user']
        recipe = self.validated_data['recipe']
        ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
