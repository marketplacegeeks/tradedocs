from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderLineItem

admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderLineItem)
