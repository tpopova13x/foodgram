# users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    #path('users/me/', CustomUserViewSet.me, name='user-me'),  # Custom me endpoint
]
