from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsManager
from .services import ReportsService


def _parse_month(request):
    today = date.today()
    try:
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))
        if not (1 <= month <= 12):
            raise ValueError
    except (TypeError, ValueError):
        year, month = today.year, today.month
    return year, month


class SalesByWaiterView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        year, month = _parse_month(request)
        return Response({
            'year': year, 'month': month,
            'rows': ReportsService.sales_by_waiter(year, month),
        })


class WaiterDetailView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        year, month = _parse_month(request)
        waiter_id = request.query_params.get('waiter')
        if not waiter_id:
            return Response({'detail': 'Informe ?waiter=<id>.'}, status=400)
        return Response({
            'year': year, 'month': month, 'waiter': int(waiter_id),
            'rows': ReportsService.waiter_detail(year, month, waiter_id),
        })


class ItemRankingView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        year, month = _parse_month(request)
        return Response({
            'year': year, 'month': month,
            'rows': ReportsService.item_ranking(year, month),
        })
