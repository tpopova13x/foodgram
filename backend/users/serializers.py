# users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField

from .models import Subscription

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Serializer for user registration."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password', 'avatar'
        )


class CustomUserSerializer(UserSerializer):
    """Serializer for user model."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'avatar'
        )

    def get_avatar(self, obj):
        """Get the full URL of the avatar or None if not set."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        """Check if authenticated user subscribed to the author."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class CustomUserResponseOnCreateSerializer(UserSerializer):
    """Serializer for response after user creation."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name'
        )


class SubscriptionSerializer(CustomUserSerializer):
    """Serializer for subscriptions."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Get recipes for the author with limit."""
        from recipes.serializers import RecipeShortSerializer

        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if limit:
            recipes = recipes[:int(limit)]

        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Count number of recipes created by the author."""
        return obj.recipes.count()


class SetAvatarSerializer(serializers.Serializer):
    """Serializer for setting user avatar."""

    avatar = Base64ImageField(required=True)


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    """Serializer for avatar update response."""

    class Meta:
        model = User
        fields = ('avatar',)