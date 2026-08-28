from django.contrib import admin

from .models import QueueTicket


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'customer_name', 'people_count', 'status', 'table', 'created_at', 'called_at', 'called_by')
    list_filter = ('status', 'created_at')
    autocomplete_fields = ('table',)
    search_fields = ('code', 'customer_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('code', 'created_at', 'called_at')
