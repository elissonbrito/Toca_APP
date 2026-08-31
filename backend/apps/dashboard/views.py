"""
Dashboard app - analytics administrativo.
"""
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.users.permissions import IsAdminMaximo
from .services import DashboardService


class DashboardView(APIView):
    """GET /api/dashboard/ - visão geral (vendas do dia/mês, mesas, fila, top produtos).

    Acesso exclusivo do ADM_MAXIMO — nenhum outro papel (nem gerente) vê o dashboard.
    """
    permission_classes = [IsAdminMaximo]

    def get(self, request):
        return Response(DashboardService.overview())
