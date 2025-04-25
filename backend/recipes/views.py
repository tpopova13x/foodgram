# recipes/views.py

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeSerializer, RecipeShortSerializer,
                          TagSerializer)


def recipe_short_link(request, id):
    """Handle short links for recipes."""
    recipe = get_object_or_404(Recipe, id=id)
    return redirect(f'/#/recipes/{recipe.id}/')


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for recipes."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.all()

        # Get tags parameter from request
        tags = self.request.query_params.getlist("tags")

        if tags:
            # Import Q for OR query construction
            from django.db.models import Q

            # Build an OR filter for tags
            tag_filter = Q()
            for tag in tags:
                tag_filter |= Q(tags__slug=tag)

            # Apply the filter and ensure distinct results
            queryset = queryset.filter(tag_filter).distinct()

        return queryset

    def update(self, request, *args, **kwargs):
        """
        Override update method to ensure all required fields
        are provided.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # For non-partial updates, ensure required fields are present
        if not partial:
            missing_fields = []

            if "ingredients" not in request.data:
                missing_fields.append("ingredients")

            if "tags" not in request.data:
                missing_fields.append("tags")

            if "image" not in request.data:
                missing_fields.append("image")
            elif not request.data["image"]:
                return Response(
                    {"image": ["This field may not be blank"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if missing_fields:
                mes = "This field is required"
                error_response = {
                    field: [mes] for field in missing_fields}
                return Response(
                    error_response,
                    status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def get_serializer_class(self):
        """Return serializer class based on action."""
        if self.action in ("create", "update", "partial_update"):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Create recipe with current user as author."""
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(detail=True, methods=["post", "delete"],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Add/remove recipe from favorites."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Recipe is already in favorites"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {"errors": "Recipe is not in favorites"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Add/remove recipe from shopping cart."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Recipe is already in shopping cart"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == "DELETE":
            cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not cart.exists():
                return Response(
                    {"errors": "Recipe is not in shopping cart"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Download shopping cart as text file."""
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__in_shopping_cart__user=request.user) .values(
                "ingredient__name",
                "ingredient__measurement_unit") .annotate(
                amount=Sum("amount")))

        if not ingredients:
            return Response({"errors": "Shopping cart is empty"},
                            status=status.HTTP_400_BAD_REQUEST)

        shopping_list = ["Список покупок:\n"]
        for ingredient in ingredients:
            name = ingredient["ingredient__name"]
            measurement_unit = ingredient["ingredient__measurement_unit"]
            amount = ingredient["amount"]
            shopping_list.append(f"• {name} - {amount} {measurement_unit}")

        response = HttpResponse(
            "\n".join(shopping_list),
            content_type="text/plain")
        response["Content-Disposition"] = (
            "attachment; filename=shopping_list.txt"
        )

        return response

    @action(
        detail=True,
        methods=["get"],
        url_path="get-link",
        permission_classes=[permissions.AllowAny],
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        base_url = request.build_absolute_uri("/").rstrip("/")
        short_link = f"{base_url}/s/{recipe.id}"

        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Override destroy method to ensure proper response."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
