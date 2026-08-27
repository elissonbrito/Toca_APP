from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CashRegisterViewSet, PaymentViewSet

router = DefaultRouter()
router.register('registers', CashRegisterViewSet, basename='cash-registers')
router.register('payments', PaymentViewSet, basename='payments')

urlpatterns = [path('', include(router.urls))]
