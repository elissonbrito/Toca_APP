from django.contrib import admin

from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'seats', 'status', 'updated_at')
    list_filter = ('status', 'seats')
    search_fields = ('number',)
    ordering = ('number',)
    readonly_fields = ('created_at', 'updated_at')
