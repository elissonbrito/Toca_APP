"""
Printing services - montagem do conteúdo e gestão da fila.
"""
from django.utils import timezone

from .models import Printer, PrintJob, PrintJobStatus, PrintSettings


class PrintingService:
    @staticmethod
    def _order_ref(order):
        if order.table_id:
            return f'MESA {order.table.number}'
        if order.queue_ticket_id:
            return f'SENHA {order.queue_ticket.code}'
        return f'COMANDA #{order.id}'

    @staticmethod
    def render_item_ticket(order, item, settings=None):
        settings = settings or PrintSettings.load()
        width = settings.paper_width or 48
        rule = '-' * width
        lines = [
            settings.header_title or 'Toca do Espanhol',
            rule,
            PrintingService._order_ref(order),
            f'Comanda #{order.id}',
            f'Emissao: {timezone.localtime().strftime("%d/%m/%Y %H:%M:%S")}',
        ]
        if item.created_by_id:
            lines.append(f'Garcom: {item.created_by.name}')
        lines += [rule, f'{item.quantity}x  {item.product_name}']
        if item.observations:
            lines.append(f'   OBS: {item.observations}')
        lines += [rule, f'Setor: {item.get_sector_display()}']
        if settings.footer_text:
            lines += [rule, settings.footer_text]
        return '\n'.join(lines)

    @staticmethod
    def enqueue_item(order, item):
        """Enfileira a impressão de um item recém-lançado.

        Cria um :class:`PrintJob` para cada impressora ativa do setor do item
        (bar e parrilla saem por padrão; cozinha sai se houver impressora
        cadastrada para ela). Sem impressora ativa no setor -> nada é enfileirado.
        """
        printers = list(Printer.objects.filter(sector=item.sector, is_active=True))
        if not printers:
            return []
        settings = PrintSettings.load()
        body = PrintingService.render_item_ticket(order, item, settings)
        return [
            PrintJob.objects.create(
                order=order, order_item=item, printer=printer, sector=item.sector,
                title=f'{item.quantity}x {item.product_name}', body=body,
            )
            for printer in printers
        ]

    @staticmethod
    def mark_printed(job):
        job.status = PrintJobStatus.IMPRESSO
        job.printed_at = timezone.now()
        job.error_message = ''
        job.save(update_fields=['status', 'printed_at', 'error_message'])
        return job

    @staticmethod
    def mark_error(job, message=''):
        job.status = PrintJobStatus.ERRO
        job.error_message = (message or '')[:300]
        job.save(update_fields=['status', 'error_message'])
        return job

    @staticmethod
    def requeue(job):
        job.status = PrintJobStatus.PENDENTE
        job.error_message = ''
        job.printed_at = None
        job.save(update_fields=['status', 'error_message', 'printed_at'])
        return job
