# users/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, UserMeView

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path(
        'users/me/',
        UserMeView.as_view(),
        name='user-me'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
]
