from django.urls import path
from .views import KitchenOrdersView, KitchenItemStatusView

urlpatterns = [
    path('orders/', KitchenOrdersView.as_view(), name='kitchen-orders'),
    path('items/<int:item_id>/status/', KitchenItemStatusView.as_view(), name='kitchen-item-status'),
]
