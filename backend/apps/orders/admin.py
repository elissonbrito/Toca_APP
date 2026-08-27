from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ('menu_item',)
    readonly_fields = ('total_price', 'fiscal_ncm', 'fiscal_csosn', 'fiscal_cfop',
                       'created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'status', 'total_amount', 'opened_by', 'created_at', 'closed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'customer_name', 'table__number')
    date_hierarchy = 'created_at'
    readonly_fields = ('total_amount', 'created_at', 'closed_at')
    inlines = [OrderItemInline]
    autocomplete_fields = ('table',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'quantity', 'unit_price', 'total_price', 'sector', 'status')
    list_filter = ('sector', 'status')
    search_fields = ('product_name', 'order__id')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
