from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PrinterViewSet, PrintJobViewSet, PrintSettingsView

router = DefaultRouter()
router.register('printers', PrinterViewSet, basename='printers')
router.register('jobs', PrintJobViewSet, basename='print-jobs')

urlpatterns = [
    path('settings/', PrintSettingsView.as_view(), name='print-settings'),
    path('', include(router.urls)),
]
