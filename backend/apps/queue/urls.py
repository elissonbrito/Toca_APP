from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QueueTicketViewSet

router = DefaultRouter()
router.register('', QueueTicketViewSet, basename='queue')

urlpatterns = [path('', include(router.urls))]
