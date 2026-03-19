from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

from apps.accounts.permissions import IsAnyRole, IsCheckerOrAdmin
from .models import Bank, Country, Currency, Incoterm, Location, Organisation, OrganisationAddress, Port, PaymentTerm, PreCarriageBy, TCTemplate, UOM
from .serializers import (
    BankSerializer, CountrySerializer, CurrencySerializer, IncotermSerializer, LocationSerializer,
    OrganisationAddressSerializer, OrganisationSerializer,
    PortSerializer, PaymentTermSerializer, PreCarriageBySerializer, TCTemplateSerializer, UOMSerializer,
)


class ReferenceDataViewSet(viewsets.ModelViewSet):
    """
    Base viewset for all lookup/reference data.
    Read access: any authenticated user (needed for dropdown population).
    Write access: Checker or Company Admin only (FR-06).
    Soft-delete: destroy sets is_active=False instead of deleting the row.
    All subclasses inherit this behaviour automatically.
    """
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAnyRole()]
        return [IsCheckerOrAdmin()]

    def get_queryset(self):
        # Default: return only active records.
        # Pass ?is_active=false to include deactivated records (admin use).
        queryset = super().get_queryset()
        is_active_param = self.request.query_params.get("is_active")
        if is_active_param is not None:
            queryset = queryset.filter(is_active=is_active_param.lower() == "true")
        else:
            queryset = queryset.filter(is_active=True)
        return queryset

    def destroy(self, request, *args, **kwargs):
        # Soft delete: mark as inactive instead of removing from the database.
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CountryViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]  # explicit per constraint #29; overridden by get_permissions()
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class PortViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = Port.objects.select_related("country").all()
    serializer_class = PortSerializer


class LocationViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = Location.objects.select_related("country").all()
    serializer_class = LocationSerializer


class IncotermViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = Incoterm.objects.all()
    serializer_class = IncotermSerializer


class UOMViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = UOM.objects.all()
    serializer_class = UOMSerializer


class PaymentTermViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer


class PreCarriageByViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = PreCarriageBy.objects.all()
    serializer_class = PreCarriageBySerializer


# ---------------------------------------------------------------------------
# Currency and Bank views (FR-05)
# ---------------------------------------------------------------------------

class CurrencyViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer

    def get_queryset(self):
        # Currency has no is_active field — return all records, bypassing the base filter.
        return Currency.objects.all()


class BankViewSet(viewsets.ModelViewSet):
    """
    CRUD for bank account records.
    Read: any authenticated user (needed for PI and CI dropdowns).
    Write: Checker or Company Admin only.
    """
    serializer_class = BankSerializer
    permission_classes = [IsAnyRole]  # overridden per method in get_permissions()

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAnyRole()]
        return [IsCheckerOrAdmin()]

    def get_queryset(self):
        queryset = Bank.objects.select_related("bank_country", "currency")
        # Default: only active banks. Pass ?is_active=false to see deactivated ones.
        is_active_param = self.request.query_params.get("is_active")
        if is_active_param is not None:
            queryset = queryset.filter(is_active=is_active_param.lower() == "true")
        else:
            queryset = queryset.filter(is_active=True)
        return queryset


# ---------------------------------------------------------------------------
# Organisation views (FR-04)
# ---------------------------------------------------------------------------

class OrganisationViewSet(viewsets.ModelViewSet):
    """
    CRUD for organisations.
    Read: any authenticated user (needed so Makers can populate document dropdowns).
    Write: Checker or Company Admin only.
    DELETE is blocked — organisations are deactivated via PATCH {is_active: false}.
    """
    serializer_class = OrganisationSerializer
    permission_classes = [IsAnyRole]  # overridden per method in get_permissions()

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAnyRole()]
        return [IsCheckerOrAdmin()]

    def get_queryset(self):
        queryset = Organisation.objects.prefetch_related(
            "addresses__country", "tags", "tax_codes"
        )

        # By default show only active organisations; pass ?is_active=false to see inactive.
        is_active_param = self.request.query_params.get("is_active")
        if is_active_param is not None:
            queryset = queryset.filter(is_active=is_active_param.lower() == "true")
        else:
            queryset = queryset.filter(is_active=True)

        # Allow filtering by tag so document forms can request e.g. ?tag=EXPORTER.
        tag = self.request.query_params.get("tag")
        if tag:
            queryset = queryset.filter(tags__tag=tag.upper())

        return queryset

    def destroy(self, request, *args, **kwargs):
        # Constraint #8: organisations must never be hard-deleted.
        raise MethodNotAllowed(
            "DELETE",
            detail="Organisations cannot be deleted. Set is_active=false to deactivate."
        )


class OrganisationAddressViewSet(viewsets.ModelViewSet):
    """
    Manages addresses for a single organisation (/organisations/{org_id}/addresses/).
    Read: any authenticated user.
    Write: Checker or Company Admin only.
    DELETE is allowed but blocked if it would remove the last address.
    """
    serializer_class = OrganisationAddressSerializer
    permission_classes = [IsAnyRole]  # overridden per method in get_permissions()

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAnyRole()]
        return [IsCheckerOrAdmin()]

    def get_queryset(self):
        # Scope all queries to the parent organisation from the URL.
        return OrganisationAddress.objects.filter(
            organisation_id=self.kwargs["organisation_pk"]
        ).select_related("country")

    def perform_create(self, serializer):
        organisation = Organisation.objects.get(pk=self.kwargs["organisation_pk"])
        serializer.save(organisation=organisation)

    def destroy(self, request, *args, **kwargs):
        address = self.get_object()
        # Prevent removing the last address — every organisation must keep at least one.
        if address.organisation.addresses.count() <= 1:
            raise ValidationError(
                "Cannot delete the only address. An organisation must have at least one address."
            )
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# T&C Template views (FR-07)
# ---------------------------------------------------------------------------

class TCTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD for Terms & Conditions templates.
    Read: any authenticated user (so Makers can select templates on document forms).
    Write: Checker or Company Admin only.
    DELETE: soft-deleted (is_active=False) — never hard-deleted.
    """
    serializer_class = TCTemplateSerializer
    permission_classes = [IsAnyRole]  # overridden per method in get_permissions()

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAnyRole()]
        return [IsCheckerOrAdmin()]

    def get_queryset(self):
        queryset = TCTemplate.objects.prefetch_related("organisations")
        # Default: return only active templates; pass ?is_active=false to see deactivated ones.
        is_active_param = self.request.query_params.get("is_active")
        if is_active_param is not None:
            queryset = queryset.filter(is_active=is_active_param.lower() == "true")
        else:
            queryset = queryset.filter(is_active=True)
        return queryset

    def destroy(self, request, *args, **kwargs):
        # Soft delete: mark as inactive instead of removing from the database.
        # This preserves templates that may already be referenced by existing documents.
        template = self.get_object()
        template.is_active = False
        template.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
