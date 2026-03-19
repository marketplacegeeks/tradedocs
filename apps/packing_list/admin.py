from django.contrib import admin

from .models import Container, ContainerItem, PackingList


class ContainerItemInline(admin.TabularInline):
    model = ContainerItem
    extra = 0
    readonly_fields = ("item_gross_weight",)


class ContainerInline(admin.TabularInline):
    model = Container
    extra = 0
    readonly_fields = ("gross_weight",)


@admin.register(PackingList)
class PackingListAdmin(admin.ModelAdmin):
    list_display = ("pl_number", "pl_date", "status", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("pl_number",)
    readonly_fields = ("pl_number", "created_at", "updated_at")
    inlines = [ContainerInline]


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ("container_ref", "packing_list", "tare_weight", "gross_weight")
    readonly_fields = ("gross_weight",)
    inlines = [ContainerItemInline]


@admin.register(ContainerItem)
class ContainerItemAdmin(admin.ModelAdmin):
    list_display = ("item_code", "container", "quantity", "uom", "item_gross_weight")
    readonly_fields = ("item_gross_weight",)
