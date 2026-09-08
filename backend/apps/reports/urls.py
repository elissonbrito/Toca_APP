from django.urls import path

from .views import SalesByWaiterView, WaiterDetailView, ItemRankingView

urlpatterns = [
    path('sales-by-waiter/', SalesByWaiterView.as_view(), name='reports-sales-by-waiter'),
    path('waiter-detail/', WaiterDetailView.as_view(), name='reports-waiter-detail'),
    path('item-ranking/', ItemRankingView.as_view(), name='reports-item-ranking'),
]
