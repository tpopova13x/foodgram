# users/views.py

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .pagination import CustomPageNumberPagination
from .serializers import (CustomUserCreateSerializer,
                          CustomUserResponseOnCreateSerializer,
                          CustomUserSerializer, SetAvatarResponseSerializer,
                          SetAvatarSerializer, SubscriptionCreateSerializer,
                          SubscriptionDeleteSerializer, SubscriptionSerializer)

User = get_user_model()


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return authenticated user's information."""
        serializer = CustomUserSerializer(
            request.user, context={'request': request})
        return Response(serializer.data)

    def handle_exception(self, exc):
        # Override handle_exception to return 401 for authentication errors
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().handle_exception(exc)


class CustomUserViewSet(UserViewSet):
    """ViewSet for users."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Override create method to use custom serializer for response."""
        serializer = CustomUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            CustomUserResponseOnCreateSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Subscribe/unsubscribe from author."""
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            serializer = SubscriptionCreateSerializer(
                data=request.data,
                context={'request': request, 'author': author}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            response_serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(response_serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            serializer = SubscriptionDeleteSerializer(
                data=request.data,
                context={'request': request, 'author': author}
            )
            serializer.is_valid(raise_exception=True)
            serializer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Get user subscriptions."""
        user = request.user
        subscriptions = User.objects.filter(subscribing__user=user)
        page = self.paginate_queryset(subscriptions)

        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            subscriptions, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Add or remove avatar for current user."""
        user = request.user

        if request.method == 'PUT':
            serializer = SetAvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Delete old avatar if exists
            if user.avatar:
                user.avatar.delete(save=False)

            user.avatar = serializer.validated_data['avatar']
            user.save()

            return Response(
                SetAvatarResponseSerializer(user).data,
                status=status.HTTP_200_OK
            )

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)
