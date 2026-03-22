"""
R-04 Commodity Sales Report endpoint.
R-05 Consignee-wise Business Summary endpoint.

R-04: Returns a flat list of line items (one row per item) from both Proforma Invoices
and Commercial Invoices, with full document context joined in Python.

R-05: Returns one aggregated row per consignee, combining PI and CI revenue and
document counts. Uses Django ORM aggregation (Sum/Count/Max) to avoid N+1 queries.

GET /api/v1/reports/commodity-sales/
GET /api/v1/reports/consignee-business-summary/

Constraint #10: explicit permission_classes on every view.
"""

from decimal import Decimal

from django.db.models import Count, Max, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsCheckerOrAdmin
from apps.commercial_invoice.models import CommercialInvoiceLineItem
from .models import ProformaInvoiceLineItem


class CommoditySalesReportView(APIView):
    """
    Flat line-item report combining PI and CI line items.
    Accessible to Checker and Company Admin only.
    """
    permission_classes = [IsAuthenticated, IsCheckerOrAdmin]

    def get(self, request):
        doc_type   = request.query_params.get("doc_type", "").upper()
        date_after = request.query_params.get("date_after", "")
        date_before = request.query_params.get("date_before", "")
        status_val = request.query_params.get("status", "")
        consignee  = request.query_params.get("consignee", "")
        hsn_code   = request.query_params.get("hsn_code", "")
        item_code  = request.query_params.get("item_code", "")
        uom        = request.query_params.get("uom", "")

        rows = []

        # ---- PI line items ---------------------------------------------------
        if doc_type in ("", "PI"):
            pi_qs = (
                ProformaInvoiceLineItem.objects
                .select_related(
                    "pi__consignee",
                    "pi__country_of_final_destination",
                    "pi__incoterms",
                    "pi__port_of_loading",
                    "uom",
                )
            )
            if date_after:
                pi_qs = pi_qs.filter(pi__pi_date__gte=date_after)
            if date_before:
                pi_qs = pi_qs.filter(pi__pi_date__lte=date_before)
            if status_val:
                pi_qs = pi_qs.filter(pi__status=status_val)
            if consignee:
                pi_qs = pi_qs.filter(pi__consignee_id=consignee)
            if hsn_code:
                pi_qs = pi_qs.filter(hsn_code__icontains=hsn_code)
            if item_code:
                pi_qs = pi_qs.filter(item_code__icontains=item_code)
            if uom:
                pi_qs = pi_qs.filter(uom_id=uom)

            for item in pi_qs:
                pi = item.pi
                rows.append({
                    "doc_type": "PI",
                    "doc_number": pi.pi_number,
                    "doc_date": str(pi.pi_date) if pi.pi_date else None,
                    "status": pi.status,
                    "consignee_name": pi.consignee.name if pi.consignee_id else None,
                    "country_of_destination": (
                        pi.country_of_final_destination.name
                        if pi.country_of_final_destination_id else None
                    ),
                    "hsn_code": item.hsn_code,
                    "item_code": item.item_code,
                    "description": item.description,
                    "quantity": str(item.quantity),
                    "uom_abbr": item.uom.abbreviation if item.uom_id else None,
                    "rate_usd": str(item.rate_usd),
                    "amount_usd": str(item.amount_usd),
                    "incoterms_code": pi.incoterms.code if pi.incoterms_id else None,
                    "port_of_loading_name": (
                        pi.port_of_loading.name if pi.port_of_loading_id else None
                    ),
                })

        # ---- CI line items ---------------------------------------------------
        if doc_type in ("", "CI"):
            ci_qs = (
                CommercialInvoiceLineItem.objects
                .select_related(
                    "ci__packing_list__consignee",
                    "ci__packing_list__country_of_final_destination",
                    "ci__packing_list__incoterms",
                    "ci__packing_list__port_of_loading",
                    "uom",
                )
            )
            if date_after:
                ci_qs = ci_qs.filter(ci__ci_date__gte=date_after)
            if date_before:
                ci_qs = ci_qs.filter(ci__ci_date__lte=date_before)
            if status_val:
                ci_qs = ci_qs.filter(ci__status=status_val)
            if consignee:
                ci_qs = ci_qs.filter(ci__packing_list__consignee_id=consignee)
            if hsn_code:
                ci_qs = ci_qs.filter(hsn_code__icontains=hsn_code)
            if item_code:
                ci_qs = ci_qs.filter(item_code__icontains=item_code)
            if uom:
                ci_qs = ci_qs.filter(uom_id=uom)

            for item in ci_qs:
                ci = item.ci
                pl = ci.packing_list
                rows.append({
                    "doc_type": "CI",
                    "doc_number": ci.ci_number,
                    "doc_date": str(ci.ci_date) if ci.ci_date else None,
                    "status": ci.status,
                    "consignee_name": pl.consignee.name if pl.consignee_id else None,
                    "country_of_destination": (
                        pl.country_of_final_destination.name
                        if pl.country_of_final_destination_id else None
                    ),
                    "hsn_code": item.hsn_code,
                    "item_code": item.item_code,
                    "description": item.description,
                    "quantity": str(item.total_quantity),
                    "uom_abbr": item.uom.abbreviation if item.uom_id else None,
                    "rate_usd": str(item.rate_usd),
                    "amount_usd": str(item.amount_usd),
                    "incoterms_code": (
                        pl.incoterms.code if pl.incoterms_id else None
                    ),
                    "port_of_loading_name": (
                        pl.port_of_loading.name if pl.port_of_loading_id else None
                    ),
                })

        # Default sort: newest document date first
        rows.sort(key=lambda r: r["doc_date"] or "", reverse=True)
        return Response(rows)


class ConsigneeBusinessSummaryView(APIView):
    """
    R-05 Consignee-wise Business Summary.

    One aggregated row per consignee combining PI and CI document counts and
    revenue totals. Uses ORM aggregation to avoid N+1 queries.

    GET /api/v1/reports/consignee-business-summary/

    Query params:
      doc_type    — "PI" | "CI" | "" (default: both)
      date_after  — ISO date lower bound (inclusive) on document date
      date_before — ISO date upper bound (inclusive) on document date
      status      — exact status filter (blank = all)
      consignee   — Organisation FK id (filter to a specific consignee)
    """

    permission_classes = [IsAuthenticated, IsCheckerOrAdmin]

    def get(self, request):
        doc_type    = request.query_params.get("doc_type", "").upper()
        date_after  = request.query_params.get("date_after", "")
        date_before = request.query_params.get("date_before", "")
        status_val  = request.query_params.get("status", "")
        consignee   = request.query_params.get("consignee", "")

        # summary keyed by consignee_id
        summary: dict[int, dict] = {}

        def _ensure(cid: int, name: str) -> dict:
            if cid not in summary:
                summary[cid] = {
                    "consignee_id": cid,
                    "consignee_name": name or "Unknown",
                    "pi_count": 0,
                    "ci_count": 0,
                    "total_pi_value": Decimal("0"),
                    "total_ci_value": Decimal("0"),
                    "latest_doc_date": None,
                }
            return summary[cid]

        def _update_date(entry: dict, new_date) -> None:
            d = str(new_date) if new_date else None
            if d and (entry["latest_doc_date"] is None or d > entry["latest_doc_date"]):
                entry["latest_doc_date"] = d

        # ---- PI aggregation by consignee ------------------------------------
        if doc_type in ("", "PI"):
            pi_qs = ProformaInvoiceLineItem.objects.filter(
                pi__consignee_id__isnull=False
            )
            if date_after:
                pi_qs = pi_qs.filter(pi__pi_date__gte=date_after)
            if date_before:
                pi_qs = pi_qs.filter(pi__pi_date__lte=date_before)
            if status_val:
                pi_qs = pi_qs.filter(pi__status=status_val)
            if consignee:
                pi_qs = pi_qs.filter(pi__consignee_id=consignee)

            pi_rows = (
                pi_qs
                .values(
                    "pi__consignee_id",
                    "pi__consignee__name",
                )
                .annotate(
                    total_amount=Sum("amount_usd"),
                    doc_count=Count("pi_id", distinct=True),
                    latest_date=Max("pi__pi_date"),
                )
            )
            for row in pi_rows:
                cid  = row["pi__consignee_id"]
                name = row["pi__consignee__name"]
                entry = _ensure(cid, name)
                entry["pi_count"]       = row["doc_count"]
                entry["total_pi_value"] = row["total_amount"] or Decimal("0")
                _update_date(entry, row["latest_date"])

        # ---- CI aggregation by consignee (via PackingList) ------------------
        if doc_type in ("", "CI"):
            ci_qs = CommercialInvoiceLineItem.objects.filter(
                ci__packing_list__consignee_id__isnull=False
            )
            if date_after:
                ci_qs = ci_qs.filter(ci__ci_date__gte=date_after)
            if date_before:
                ci_qs = ci_qs.filter(ci__ci_date__lte=date_before)
            if status_val:
                ci_qs = ci_qs.filter(ci__status=status_val)
            if consignee:
                ci_qs = ci_qs.filter(ci__packing_list__consignee_id=consignee)

            ci_rows = (
                ci_qs
                .values(
                    "ci__packing_list__consignee_id",
                    "ci__packing_list__consignee__name",
                )
                .annotate(
                    total_amount=Sum("amount_usd"),
                    doc_count=Count("ci_id", distinct=True),
                    latest_date=Max("ci__ci_date"),
                )
            )
            for row in ci_rows:
                cid  = row["ci__packing_list__consignee_id"]
                name = row["ci__packing_list__consignee__name"]
                entry = _ensure(cid, name)
                entry["ci_count"]       = row["doc_count"]
                entry["total_ci_value"] = row["total_amount"] or Decimal("0")
                _update_date(entry, row["latest_date"])

        # ---- Build response rows -------------------------------------------
        rows = []
        for entry in summary.values():
            total = entry["total_pi_value"] + entry["total_ci_value"]
            rows.append({
                "consignee_id":    entry["consignee_id"],
                "consignee_name":  entry["consignee_name"],
                "pi_count":        entry["pi_count"],
                "ci_count":        entry["ci_count"],
                "total_pi_value":  str(entry["total_pi_value"]),
                "total_ci_value":  str(entry["total_ci_value"]),
                "total_value":     str(total),
                "latest_doc_date": entry["latest_doc_date"],
            })

        # Default sort: highest combined revenue first
        rows.sort(key=lambda r: Decimal(r["total_value"]), reverse=True)
        return Response(rows)
