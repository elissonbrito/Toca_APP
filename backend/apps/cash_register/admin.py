from django.contrib import admin

from .models import CashRegister, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('order', 'amount', 'payment_method', 'received_by', 'paid_at')
    can_delete = False


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'initial_amount', 'final_amount', 'opened_by', 'opened_at', 'closed_at')
    list_filter = ('status', 'opened_at')
    date_hierarchy = 'opened_at'
    readonly_fields = ('opened_by', 'closed_by', 'opened_at', 'closed_at')
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'payment_method', 'cash_register', 'received_by', 'paid_at')
    list_filter = ('payment_method', 'paid_at')
    search_fields = ('order__id',)
    date_hierarchy = 'paid_at'
    readonly_fields = ('order', 'cash_register', 'amount', 'payment_method', 'received_by', 'paid_at')

    def has_change_permission(self, request, obj=None):
        return False
