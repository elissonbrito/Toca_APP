from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsManager
from apps.audit.services import AuditService
from .models import Printer, PrintSettings, PrintJob, PrintJobStatus
from .serializers import PrinterSerializer, PrintSettingsSerializer, PrintJobSerializer
from .services import PrintingService


class PrinterViewSet(viewsets.ModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsManager()]

    def perform_create(self, serializer):
        printer = serializer.save()
        AuditService.log(user=self.request.user, action='CREATE', entity='Printer',
                         entity_id=printer.id, details=f'Impressora {printer.name} criada',
                         request=self.request)

    def perform_update(self, serializer):
        printer = serializer.save()
        AuditService.log(user=self.request.user, action='UPDATE', entity='Printer',
                         entity_id=printer.id, details=f'Impressora {printer.name} atualizada',
                         request=self.request)

    def perform_destroy(self, instance):
        AuditService.log(user=self.request.user, action='DELETE', entity='Printer',
                         entity_id=instance.id, details=f'Impressora {instance.name} removida',
                         request=self.request)
        instance.delete()


class PrintSettingsView(RetrieveUpdateAPIView):
    serializer_class = PrintSettingsSerializer

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method in ('GET', 'HEAD') else [IsManager()]

    def get_object(self):
        return PrintSettings.load()

    def perform_update(self, serializer):
        serializer.save()
        AuditService.log(user=self.request.user, action='UPDATE', entity='PrintSettings',
                         entity_id=1, details='Configuração de impressão atualizada',
                         request=self.request)


class PrintJobViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = PrintJobSerializer
    permission_classes = [IsAuthenticated]
    queryset = PrintJob.objects.select_related('printer', 'order', 'order_item').all()

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        sector = self.request.query_params.get('sector')
        if sector:
            qs = qs.filter(sector=sector)
        return qs.order_by('id')

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        qs = (PrintJob.objects.select_related('printer', 'order', 'order_item')
              .filter(status=PrintJobStatus.PENDENTE).order_by('id'))
        return Response(PrintJobSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='mark-printed')
    def mark_printed(self, request, pk=None):
        return Response(PrintJobSerializer(PrintingService.mark_printed(self.get_object())).data)

    @action(detail=True, methods=['post'], url_path='mark-error')
    def mark_error(self, request, pk=None):
        job = PrintingService.mark_error(self.get_object(), request.data.get('message', ''))
        return Response(PrintJobSerializer(job).data)

    @action(detail=True, methods=['post'], url_path='reprint')
    def reprint(self, request, pk=None):
        return Response(PrintJobSerializer(PrintingService.requeue(self.get_object())).data)
