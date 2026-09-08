from django.contrib import admin

from .models import Printer, PrintSettings, PrintJob


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector', 'qz_printer_name', 'is_active', 'copies')
    list_filter = ('sector', 'is_active')


@admin.register(PrintSettings)
class PrintSettingsAdmin(admin.ModelAdmin):
    list_display = ('header_title', 'paper_width', 'font_size', 'bold', 'cut_paper')


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'sector', 'title', 'status', 'printer', 'created_at', 'printed_at')
    list_filter = ('status', 'sector')
    search_fields = ('title', 'body')
