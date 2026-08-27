"""
Dashboard app - analytics administrativo.
"""
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.users.permissions import IsManager
from .services import DashboardService


class DashboardView(APIView):
    """GET /api/dashboard/ - visão geral (vendas do dia/mês, mesas, fila, top produtos)."""
    permission_classes = [IsManager]

    def get(self, request):
        return Response(DashboardService.overview())
