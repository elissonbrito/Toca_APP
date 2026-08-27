"""
Tables services - transições de status de mesa fora das views.
"""
from rest_framework.exceptions import ValidationError

from .models import Table, TableStatus


class TableService:
    @staticmethod
    def change_status(table, new_status):
        """Valida e aplica um novo status na mesa."""
        if new_status not in TableStatus.values:
            raise ValidationError({'status': 'Status inválido.'})
        table.status = new_status
        table.save(update_fields=['status', 'updated_at'])
        return table

    @staticmethod
    def free_table(table):
        return TableService.change_status(table, TableStatus.LIVRE)
