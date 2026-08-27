from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('nfce', views.InvoiceViewSet, basename='nfce')

urlpatterns = [
    path('settings/', views.FiscalSettingsView.as_view(), name='fiscal-settings'),
    path('nfce/from-order/<int:order_id>/', views.build_from_order, name='nfce-from-order'),
    path('nfce/<int:pk>/sign/', views.sign_invoice, name='nfce-sign'),
    path('nfce/<int:pk>/transmit/', views.transmit_invoice, name='nfce-transmit'),
    path('nfce/<int:pk>/xml/', views.invoice_xml, name='nfce-xml'),
    path('', include(router.urls)),
]
