from django.contrib import admin

from .models import QueueTicket


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'customer_name', 'people_count', 'status', 'created_at', 'called_at', 'called_by')
    list_filter = ('status', 'created_at')
    search_fields = ('code', 'customer_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('code', 'created_at', 'called_at')
