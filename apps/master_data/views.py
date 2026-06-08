from django.db.models.deletion import ProtectedError

from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.accounts.permissions import IsAnyRole, IsCheckerOrAdmin
from .models import (
    Bank, Country, Currency, Incoterm, Location, Organisation, OrganisationAddress, Port,
    PaymentTerm, PreCarriageBy, TCTemplate, TypeOfPackage, UOM,
    Product, ProductGrade, TestParameter, TestMethod, ProductTestTemplate, ProductTestTemplateRow,
)
from .serializers import (
    BankSerializer, CountrySerializer, CurrencySerializer, IncotermSerializer, LocationSerializer,
    OrganisationAddressSerializer, OrganisationSerializer,
    PortSerializer, PaymentTermSerializer, PreCarriageBySerializer, TCTemplateSerializer,
    TypeOfPackageSerializer, UOMSerializer,
    ProductSerializer, ProductGradeSerializer, TestParameterSerializer, TestMethodSerializer,
    ProductTestTemplateSerializer, ProductTestTemplateRowSerializer,
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


class TypeOfPackageViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = TypeOfPackage.objects.all()
    serializer_class = TypeOfPackageSerializer


# ---------------------------------------------------------------------------
# Currency and Bank views (FR-05)
# ---------------------------------------------------------------------------

class CurrencyViewSet(ReferenceDataViewSet):
    permission_classes = [IsAnyRole]
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # SUPER_ADMIN: hard-delete if no documents reference this bank.
        if request.user.role == UserRole.SUPER_ADMIN:
            try:
                instance.delete()
            except ProtectedError:
                raise ValidationError({
                    "detail": (
                        "This bank is referenced by existing documents (Proforma Invoices, "
                        "Commercial Invoices, or Purchase Orders) and cannot be deleted."
                    )
                })
            return Response(status=status.HTTP_204_NO_CONTENT)
        # All other roles: soft-delete (deactivate).
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
            "addresses__country", "tags"
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
        # SUPER_ADMIN can hard-delete an organisation only if no documents reference it.
        # All other roles are blocked (Constraint #8: never hard-delete organisations).
        if request.user.role == UserRole.SUPER_ADMIN:
            instance = self.get_object()
            try:
                instance.delete()
            except ProtectedError:
                raise ValidationError({
                    "detail": (
                        "This organisation is referenced by existing documents (Proforma Invoices, "
                        "Packing Lists, or Purchase Orders) and cannot be deleted."
                    )
                })
            return Response(status=status.HTTP_204_NO_CONTENT)
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
        template = self.get_object()
        # SUPER_ADMIN: hard-delete if no documents reference this template.
        if request.user.role == UserRole.SUPER_ADMIN:
            try:
                template.delete()
            except ProtectedError:
                raise ValidationError({
                    "detail": (
                        "This template is referenced by existing documents (Proforma Invoices or "
                        "Purchase Orders) and cannot be deleted."
                    )
                })
            return Response(status=status.HTTP_204_NO_CONTENT)
        # All other roles: soft-delete so templates on existing documents are preserved.
        template.is_active = False
        template.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# COA Master Data views
# ---------------------------------------------------------------------------

class ProductViewSet(ReferenceDataViewSet):
    """CRUD for chemical products. Read: any role. Write: Checker or Admin."""
    permission_classes = [IsAnyRole]
    queryset = Product.objects.prefetch_related("grades").all()
    serializer_class = ProductSerializer

    def destroy(self, request, *args, **kwargs):
        # Soft-delete: deactivate the product and cascade deactivation to all its grades.
        instance = self.get_object()
        instance.is_active = False
        instance.grades.update(is_active=False)
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductGradeViewSet(viewsets.ModelViewSet):
    """
    Manages grades for a single product (/products/{product_pk}/grades/).
    Read: any role. Write: Checker or Admin.
    """
    serializer_class = ProductGradeSerializer
    permission_classes = [IsAnyRole]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAnyRole()]
        return [IsCheckerOrAdmin()]

    def get_queryset(self):
        # Scope to the parent product from the URL kwargs.
        return ProductGrade.objects.filter(
            product_id=self.kwargs["product_pk"]
        ).select_related("product")

    def perform_create(self, serializer):
        # Inject the parent product from the URL so the caller doesn't have to send product_id.
        product = Product.objects.get(pk=self.kwargs["product_pk"])
        serializer.save(product=product)


class TestParameterViewSet(ReferenceDataViewSet):
    """CRUD for test parameter library. Read: any role. Write: Checker or Admin."""
    permission_classes = [IsAnyRole]
    queryset = TestParameter.objects.select_related("default_unit").all()
    serializer_class = TestParameterSerializer


class TestMethodViewSet(ReferenceDataViewSet):
    """CRUD for test method library. Read: any role. Write: Checker or Admin."""
    permission_classes = [IsAnyRole]
    queryset = TestMethod.objects.all()
    serializer_class = TestMethodSerializer


class ProductTestTemplateView(APIView):
    """
    GET  /api/product-grades/{id}/test-template/ — returns template rows for a grade.
    PUT  /api/product-grades/{id}/test-template/ — replaces all rows (Checker/Admin only).
    """
    permission_classes = [IsAnyRole]

    def get(self, request, product_grade_pk):
        from rest_framework.exceptions import NotFound
        try:
            grade = ProductGrade.objects.get(pk=product_grade_pk)
        except ProductGrade.DoesNotExist:
            raise NotFound("ProductGrade not found.")
        try:
            template = ProductTestTemplate.objects.prefetch_related("rows").get(product_grade=grade)
            serializer = ProductTestTemplateSerializer(template)
            return Response(serializer.data)
        except ProductTestTemplate.DoesNotExist:
            # No template saved yet — return an empty structure so the frontend can render the form.
            return Response({"id": None, "product_grade": grade.pk, "updated_at": None, "rows": []})

    def put(self, request, product_grade_pk):
        from rest_framework.exceptions import NotFound, PermissionDenied
        # Only Checker, Company Admin, or Super Admin may save templates.
        if request.user.role not in (UserRole.CHECKER, UserRole.COMPANY_ADMIN, UserRole.SUPER_ADMIN):
            raise PermissionDenied("Only Checker or Company Admin can save test templates.")
        try:
            grade = ProductGrade.objects.get(pk=product_grade_pk)
        except ProductGrade.DoesNotExist:
            raise NotFound("ProductGrade not found.")
        rows_data = request.data.get("rows", [])
        # Validate all rows up-front before touching the database.
        row_serializer = ProductTestTemplateRowSerializer(data=rows_data, many=True)
        row_serializer.is_valid(raise_exception=True)
        # Get or create the parent template record.
        template, _ = ProductTestTemplate.objects.get_or_create(product_grade=grade)
        # Replace all existing rows with the submitted set.
        template.rows.all().delete()
        for row_data in row_serializer.validated_data:
            ProductTestTemplateRow.objects.create(template=template, **row_data)
        # Return the freshly saved template.
        refreshed = ProductTestTemplate.objects.prefetch_related("rows").get(pk=template.pk)
        serializer = ProductTestTemplateSerializer(refreshed)
        return Response(serializer.data)
