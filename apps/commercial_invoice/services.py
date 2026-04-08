"""
CommercialInvoice service — document-level business logic.

Constraint #16: CI numbers are generated inside select_for_update() to prevent duplicates.
Constraint #17: Format is CI-YYYY-NNNN (4-digit, zero-padded sequence per year).
"""

from collections import defaultdict
from datetime import date

from django.db import transaction


def rebuild_ci_line_items(packing_list):
    """
    Regenerate CommercialInvoiceLineItems from the PL's ContainerItems.

    Groups items by (item_code, uom_id) across all containers. Creates new rows,
    updates existing ones, and deletes rows that no longer have a matching group.
    Existing rate_usd values are preserved so the Maker doesn't lose entered rates.

    Called whenever containers or container items are created, updated, or deleted.
    Must be called inside a transaction if the caller is already within one.
    """
    from .models import CommercialInvoice, CommercialInvoiceLineItem

    try:
        ci = packing_list.commercial_invoice
    except CommercialInvoice.DoesNotExist:
        return  # CI not yet created — nothing to rebuild

    # Aggregate all ContainerItems across all containers for this PL.
    # total_quantity is the sum of net_material_weight (no_of_packages × qty_per_package)
    # across all items with the same item_code + uom.
    groups = defaultdict(lambda: {
        "total_quantity": 0,
        "description": "",
        "hsn_code": "",
        "uom_id": None,
    })

    for container in packing_list.containers.prefetch_related("items__uom").all():
        for item in container.items.all():
            key = (item.item_code, item.uom_id)
            groups[key]["total_quantity"] += item.net_material_weight
            groups[key]["uom_id"] = item.uom_id
            # Use the first non-empty value for description and hsn_code.
            if not groups[key]["description"]:
                groups[key]["description"] = item.description
            if not groups[key]["hsn_code"] and item.hsn_code:
                groups[key]["hsn_code"] = item.hsn_code

    # Build a map of existing CI line items keyed by (item_code, uom_id).
    existing = {
        (li.item_code, li.uom_id): li
        for li in ci.line_items.all()
    }

    seen_keys = set()
    for (item_code, uom_id), data in groups.items():
        key = (item_code, uom_id)
        seen_keys.add(key)
        if key in existing:
            # Update aggregate fields; preserve rate_usd.
            li = existing[key]
            li.description = data["description"]
            li.hsn_code = data["hsn_code"]
            li.total_quantity = data["total_quantity"]
            # Recompute amount using existing rate.
            li.amount_usd = li.total_quantity * li.rate_usd
            li.save(update_fields=["description", "hsn_code", "total_quantity", "amount_usd"])
        else:
            # New item group — create with rate_usd = 0 (Maker will fill it in Final Rates).
            from decimal import Decimal
            CommercialInvoiceLineItem.objects.create(
                ci=ci,
                item_code=item_code,
                description=data["description"],
                hsn_code=data["hsn_code"],
                uom_id=uom_id,
                total_quantity=data["total_quantity"],
                rate_usd=Decimal("0.00"),
                amount_usd=Decimal("0.00"),
            )

    # Delete CI line items whose item_code+uom no longer exists in any container.
    for key, li in existing.items():
        if key not in seen_keys:
            li.delete()


def generate_document_number():
    """
    Generate the next CI number for the current year.
    Uses select_for_update() to lock all existing CI rows for this year,
    preventing duplicate numbers when two users save simultaneously.
    """
    from .models import CommercialInvoice  # local import avoids circular dependency at module load

    year = date.today().year
    prefix = f"CI-{year}-"

    with transaction.atomic():
        # Lock all CI rows for this year — any concurrent writer will block until we commit.
        count = (
            CommercialInvoice.objects
            .select_for_update()
            .filter(ci_number__startswith=prefix)
            .count()
        )
        return f"{prefix}{count + 1:04d}"
