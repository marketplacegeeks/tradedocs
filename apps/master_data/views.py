from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS

from apps.accounts.permissions import IsAnyRole, IsCheckerOrAdmin
from .models import Country, Incoterm, Location, Port, PaymentTerm, PreCarriageBy, UOM
from .serializers import (
    CountrySerializer, IncotermSerializer, LocationSerializer,
    PortSerializer, PaymentTermSerializer, PreCarriageBySerializer, UOMSerializer,
)


class ReferenceDataViewSet(viewsets.ModelViewSet):
    """
    Base viewset for all lookup/reference data.
    Read access: any authenticated user (needed for dropdown population).
    Write access: Checker or Company Admin only (FR-06).
    All subclasses inherit this permission split automatically.
    """
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAnyRole()]
        return [IsCheckerOrAdmin()]


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
