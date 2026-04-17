from django.contrib import admin

from .models import CommercialInvoice, CommercialInvoiceLineItem


class CommercialInvoiceLineItemInline(admin.TabularInline):
    model = CommercialInvoiceLineItem
    extra = 0
    readonly_fields = ("amount",)


@admin.register(CommercialInvoice)
class CommercialInvoiceAdmin(admin.ModelAdmin):
    list_display = ("ci_number", "ci_date", "status", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("ci_number",)
    readonly_fields = ("ci_number", "created_at", "updated_at")
    inlines = [CommercialInvoiceLineItemInline]


@admin.register(CommercialInvoiceLineItem)
class CommercialInvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ("item_code", "ci", "total_quantity", "rate", "amount")
    readonly_fields = ("amount",)
