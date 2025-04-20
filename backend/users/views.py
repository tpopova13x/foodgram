# users/views.py

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet

from .models import Subscription
from .serializers import (
    CustomUserSerializer,
    CustomUserCreateSerializer,
    CustomUserResponseOnCreateSerializer,
    SubscriptionSerializer, SetAvatarSerializer, SetAvatarResponseSerializer
)
from .pagination import CustomPageNumberPagination

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """ViewSet for users."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPageNumberPagination  # Explicitly set pagination class

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
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'You cannot subscribe to yourself'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'error': 'You are already subscribed to this author'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user, author=author
            )
            if not subscription.exists():
                return Response(
                    {'error': 'You are not subscribed to this author'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription.delete()
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


