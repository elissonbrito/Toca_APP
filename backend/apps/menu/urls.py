from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MenuCategoryViewSet, MenuItemViewSet

router = DefaultRouter()
router.register('categories', MenuCategoryViewSet, basename='menu-categories')
router.register('items', MenuItemViewSet, basename='menu-items')

urlpatterns = [path('', include(router.urls))]
