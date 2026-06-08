import factory
from apps.accounts.tests.factories import MakerFactory
from apps.certificate_of_analysis.models import CertificateOfAnalysis, COAParameter
from apps.master_data.tests.factories import (
    OrganisationFactory, OrganisationTagFactory, UOMFactory, TypeOfPackageFactory,
)


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "master_data.Product"

    name = factory.Sequence(lambda n: f"Chemical {n}")
    cas_number = factory.Sequence(lambda n: f"{n:02d}-{n:02d}-{n}")
    is_active = True


class ProductGradeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "master_data.ProductGrade"

    product = factory.SubFactory(ProductFactory)
    grade = factory.Sequence(lambda n: f"Grade {n}")
    is_active = True


class TestParameterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "master_data.TestParameter"

    name = factory.Sequence(lambda n: f"Test Parameter {n}")
    default_unit = None
    is_active = True


class TestMethodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "master_data.TestMethod"

    code = factory.Sequence(lambda n: f"METH-{n:03d}")
    description = factory.Sequence(lambda n: f"Method Description {n}")
    is_active = True


class ProductTestTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "master_data.ProductTestTemplate"

    product_grade = factory.SubFactory(ProductGradeFactory)


class ProductTestTemplateRowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "master_data.ProductTestTemplateRow"

    template = factory.SubFactory(ProductTestTemplateFactory)
    s_no = factory.Sequence(lambda n: n + 1)
    spec_type = "QUALITATIVE"
    spec_description = "Complies"


def make_org_with_tag(tag):
    """Helper: create an Organisation and attach the given role tag to it."""
    org = OrganisationFactory()
    OrganisationTagFactory(organisation=org, tag=tag)
    return org


class CertificateOfAnalysisFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CertificateOfAnalysis

    coa_number = factory.Sequence(lambda n: f"COA-2026-{n + 1:04d}")
    product_grade = factory.SubFactory(ProductGradeFactory)
    customer = factory.LazyFunction(lambda: make_org_with_tag("CONSIGNEE"))
    batch_number = factory.Sequence(lambda n: f"BATCH-{n:04d}")
    package_count = 10
    package_volume = "1000.000"
    package_uom = factory.SubFactory(UOMFactory)
    package_type = factory.SubFactory(TypeOfPackageFactory)
    date_of_manufacture = "2025-12-22"
    date_of_retest = "2026-12-21"
    date_time_of_sampling = "2025-12-25T18:00:00Z"
    date_time_of_analysis = "2025-12-25T19:25:00Z"
    analyst_name = "Test Analyst"
    qc_incharge_name = "Test QC"
    footer_organisation = factory.LazyFunction(lambda: make_org_with_tag("EXPORTER"))
    status = "DRAFT"
    created_by = factory.SubFactory(MakerFactory)


class COAParameterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = COAParameter

    coa = factory.SubFactory(CertificateOfAnalysisFactory)
    s_no = factory.Sequence(lambda n: n + 1)
    spec_type = "QUALITATIVE"
    spec_description = "Complies"
    result_text = "Complies"
