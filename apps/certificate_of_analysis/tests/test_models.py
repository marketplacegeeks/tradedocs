"""
Model-level tests for CertificateOfAnalysis, COAParameter, and related master data models.
"""
import pytest
from apps.certificate_of_analysis.models import CertificateOfAnalysis, COAParameter
from .factories import (
    CertificateOfAnalysisFactory,
    COAParameterFactory,
    ProductFactory,
    ProductGradeFactory,
    ProductTestTemplateFactory,
    ProductTestTemplateRowFactory,
)


@pytest.mark.django_db
class TestCertificateOfAnalysisModel:

    def test_coa_str(self):
        coa = CertificateOfAnalysisFactory()
        assert str(coa) == coa.coa_number

    def test_coa_default_status_is_draft(self):
        coa = CertificateOfAnalysisFactory()
        assert coa.status == "DRAFT"

    def test_coa_number_is_unique(self):
        CertificateOfAnalysisFactory(coa_number="COA-2026-0001")
        with pytest.raises(Exception):
            CertificateOfAnalysisFactory(coa_number="COA-2026-0001")

    def test_coa_str_matches_coa_number(self):
        coa = CertificateOfAnalysisFactory(coa_number="COA-2026-0099")
        assert str(coa) == "COA-2026-0099"

    def test_coa_ordering_newest_first(self):
        """Meta ordering is [-created_at]; newest record comes first."""
        coa1 = CertificateOfAnalysisFactory()
        coa2 = CertificateOfAnalysisFactory()
        coas = list(CertificateOfAnalysis.objects.all())
        # coa2 was created after coa1, so it appears first in the default ordering.
        assert coas[0].pk == coa2.pk
        assert coas[1].pk == coa1.pk


@pytest.mark.django_db
class TestCOAParameterModel:

    def test_parameter_str_contains_coa_number(self):
        param = COAParameterFactory()
        assert param.coa.coa_number in str(param)

    def test_qualitative_parameter_saves(self):
        param = COAParameterFactory(
            spec_type="QUALITATIVE",
            spec_description="Clear, colourless liquid",
            result_text="Complies",
        )
        assert param.pk is not None
        assert param.spec_type == "QUALITATIVE"

    def test_quantitative_parameter_saves(self):
        param = COAParameterFactory(
            spec_type="QUANTITATIVE",
            spec_min="99.900000",
            spec_max=None,
            result_value="99.960000",
            result_text="",
            spec_description="",
        )
        assert param.pk is not None
        assert param.spec_type == "QUANTITATIVE"

    def test_parameters_ordered_by_s_no(self):
        """COAParameter.Meta.ordering = ['s_no'] — rows come back sorted."""
        coa = CertificateOfAnalysisFactory()
        COAParameterFactory(coa=coa, s_no=3)
        COAParameterFactory(coa=coa, s_no=1)
        COAParameterFactory(coa=coa, s_no=2)
        rows = list(coa.parameters.all())
        assert rows[0].s_no == 1
        assert rows[1].s_no == 2
        assert rows[2].s_no == 3

    def test_parameter_cascade_deleted_with_coa(self):
        """CASCADE on the coa FK means parameters are deleted when the COA is deleted."""
        coa = CertificateOfAnalysisFactory()
        param = COAParameterFactory(coa=coa)
        param_id = param.pk
        coa.delete()
        assert not COAParameter.objects.filter(pk=param_id).exists()


@pytest.mark.django_db
class TestProductMasterModel:

    def test_product_str(self):
        product = ProductFactory(name="Chloroform")
        assert str(product) == "Chloroform"

    def test_product_grade_unique_together(self):
        grade = ProductGradeFactory(grade="Technical")
        with pytest.raises(Exception):
            ProductGradeFactory(product=grade.product, grade="Technical")

    def test_product_grade_str_contains_product_name(self):
        grade = ProductGradeFactory()
        assert grade.product.name in str(grade)


@pytest.mark.django_db
class TestProductTestTemplate:

    def test_template_linked_to_product_grade(self):
        template = ProductTestTemplateFactory()
        assert template.product_grade is not None

    def test_template_rows_ordered_by_s_no(self):
        template = ProductTestTemplateFactory()
        ProductTestTemplateRowFactory(template=template, s_no=3)
        ProductTestTemplateRowFactory(template=template, s_no=1)
        ProductTestTemplateRowFactory(template=template, s_no=2)
        rows = list(template.rows.all())
        assert rows[0].s_no == 1
        assert rows[1].s_no == 2
        assert rows[2].s_no == 3

    def test_template_one_to_one_with_product_grade(self):
        """ProductGrade.test_template reverse accessor returns the one template."""
        template = ProductTestTemplateFactory()
        pg = template.product_grade
        assert pg.test_template.pk == template.pk
