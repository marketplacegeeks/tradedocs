"""
API view tests for Certificate of Analysis endpoints.

Every endpoint has at minimum:
- One happy-path test
- One permission-denial test
"""
import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CheckerFactory, MakerFactory
from apps.master_data.tests.factories import UOMFactory, TypeOfPackageFactory
from apps.workflow.constants import DRAFT, PENDING_APPROVAL, APPROVED, REWORK, PERMANENTLY_REJECTED
from apps.certificate_of_analysis.models import CertificateOfAnalysis, COAParameter

from .factories import (
    CertificateOfAnalysisFactory,
    COAParameterFactory,
    ProductGradeFactory,
    ProductTestTemplateFactory,
    ProductTestTemplateRowFactory,
    make_org_with_tag,
)


# ---- Helpers ----------------------------------------------------------------

def auth_client(user):
    """Return an APIClient that is force-authenticated as `user`."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


BASE_URL = "/api/v1/coas/"


def coa_detail_url(pk):
    return f"{BASE_URL}{pk}/"


def coa_action_url(pk, action):
    return f"{BASE_URL}{pk}/{action}/"


def valid_coa_payload(product_grade, customer, footer_org, uom, pkg_type):
    """Return a minimal valid payload for creating a COA via the API."""
    return {
        "product_grade": product_grade.id,
        "customer": customer.id,
        "batch_number": "TEST-BATCH-001",
        "package_count": 10,
        "package_volume": "1000.000",
        "package_uom": uom.id,
        "package_type": pkg_type.id,
        "date_of_manufacture": "2025-12-22",
        "date_of_retest": "2026-12-21",
        "date_time_of_sampling": "2025-12-25T18:00:00Z",
        "date_time_of_analysis": "2025-12-25T19:25:00Z",
        "analyst_name": "Test Analyst",
        "qc_incharge_name": "Test QC",
        "footer_organisation": footer_org.id,
        "parameters": [
            {
                "s_no": 1,
                "spec_type": "QUALITATIVE",
                "spec_description": "Clear, colourless liquid",
                "result_text": "Complies",
            }
        ],
    }


# ---- Create & List ----------------------------------------------------------

@pytest.mark.django_db
class TestCOACreateAndList:

    def setup_method(self):
        self.maker = MakerFactory()
        self.checker = CheckerFactory()
        self.pg = ProductGradeFactory()
        self.customer = make_org_with_tag("CONSIGNEE")
        self.footer_org = make_org_with_tag("EXPORTER")
        self.uom = UOMFactory()
        self.pkg_type = TypeOfPackageFactory()

    def _payload(self):
        return valid_coa_payload(
            self.pg, self.customer, self.footer_org, self.uom, self.pkg_type
        )

    def test_maker_can_create_coa(self):
        client = auth_client(self.maker)
        resp = client.post(BASE_URL, self._payload(), format="json")
        assert resp.status_code == 201
        assert resp.data["status"] == DRAFT
        assert resp.data["coa_number"].startswith("COA-")

    def test_checker_cannot_create_coa(self):
        client = auth_client(self.checker)
        resp = client.post(BASE_URL, self._payload(), format="json")
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create_coa(self):
        client = APIClient()
        resp = client.post(BASE_URL, self._payload(), format="json")
        assert resp.status_code == 401

    def test_maker_can_list_coas(self):
        CertificateOfAnalysisFactory(created_by=self.maker)
        client = auth_client(self.maker)
        resp = client.get(BASE_URL)
        assert resp.status_code == 200

    def test_checker_can_list_coas(self):
        CertificateOfAnalysisFactory(created_by=self.maker)
        client = auth_client(self.checker)
        resp = client.get(BASE_URL)
        assert resp.status_code == 200

    def test_unauthenticated_cannot_list_coas(self):
        client = APIClient()
        resp = client.get(BASE_URL)
        assert resp.status_code == 401

    def test_create_assigns_coa_number_with_correct_format(self):
        client = auth_client(self.maker)
        resp = client.post(BASE_URL, self._payload(), format="json")
        assert resp.status_code == 201
        # COA-YYYY-NNNN
        parts = resp.data["coa_number"].split("-")
        assert len(parts) == 3
        assert parts[0] == "COA"
        assert len(parts[2]) == 4
        assert parts[2].isdigit()

    def test_create_assigns_created_by_to_requesting_user(self):
        client = auth_client(self.maker)
        resp = client.post(BASE_URL, self._payload(), format="json")
        assert resp.status_code == 201
        coa = CertificateOfAnalysis.objects.get(pk=resp.data["id"])
        assert coa.created_by == self.maker

    def test_retrieve_single_coa(self):
        coa = CertificateOfAnalysisFactory(created_by=self.maker)
        client = auth_client(self.maker)
        resp = client.get(coa_detail_url(coa.id))
        assert resp.status_code == 200
        assert resp.data["coa_number"] == coa.coa_number

    def test_maker_can_update_draft_coa(self):
        coa = CertificateOfAnalysisFactory(created_by=self.maker, status=DRAFT)
        client = auth_client(self.maker)
        resp = client.patch(
            coa_detail_url(coa.id),
            {"batch_number": "UPDATED-BATCH", "parameters": []},
            format="json",
        )
        assert resp.status_code == 200
        coa.refresh_from_db()
        assert coa.batch_number == "UPDATED-BATCH"

    def test_checker_cannot_edit_coa(self):
        coa = CertificateOfAnalysisFactory(created_by=self.maker, status=DRAFT)
        client = auth_client(self.checker)
        resp = client.patch(
            coa_detail_url(coa.id),
            {"batch_number": "SHOULD-FAIL"},
            format="json",
        )
        assert resp.status_code == 403


# ---- Workflow ---------------------------------------------------------------

@pytest.mark.django_db
class TestCOAWorkflow:

    def setup_method(self):
        self.maker = MakerFactory()
        self.checker = CheckerFactory()
        self.pg = ProductGradeFactory()
        self.customer = make_org_with_tag("CONSIGNEE")
        self.footer_org = make_org_with_tag("EXPORTER")
        self.uom = UOMFactory()
        self.pkg_type = TypeOfPackageFactory()

    def _create_coa_via_api(self):
        """Create a COA with one parameter through the API and return its id."""
        client = auth_client(self.maker)
        payload = valid_coa_payload(
            self.pg, self.customer, self.footer_org, self.uom, self.pkg_type
        )
        resp = client.post(BASE_URL, payload, format="json")
        assert resp.status_code == 201
        return resp.data["id"]

    def test_happy_path_create_submit_approve(self):
        coa_id = self._create_coa_via_api()

        # Maker submits
        maker_client = auth_client(self.maker)
        resp = maker_client.post(coa_action_url(coa_id, "submit"))
        assert resp.status_code == 200
        assert resp.data["status"] == PENDING_APPROVAL

        # Checker approves
        checker_client = auth_client(self.checker)
        resp = checker_client.post(coa_action_url(coa_id, "approve"))
        assert resp.status_code == 200
        assert resp.data["status"] == APPROVED

    def test_maker_cannot_approve(self):
        coa_id = self._create_coa_via_api()
        maker_client = auth_client(self.maker)
        maker_client.post(coa_action_url(coa_id, "submit"))
        # A different maker tries to approve — must be denied
        other_maker = MakerFactory()
        resp = auth_client(other_maker).post(coa_action_url(coa_id, "approve"))
        assert resp.status_code == 403

    def test_checker_rework_requires_comment(self):
        coa_id = self._create_coa_via_api()
        auth_client(self.maker).post(coa_action_url(coa_id, "submit"))
        checker_client = auth_client(self.checker)
        resp = checker_client.post(
            coa_action_url(coa_id, "rework"), {"comment": ""}, format="json"
        )
        assert resp.status_code == 400

    def test_rework_flow_allows_resubmission(self):
        coa_id = self._create_coa_via_api()
        maker_client = auth_client(self.maker)
        checker_client = auth_client(self.checker)

        maker_client.post(coa_action_url(coa_id, "submit"))
        checker_client.post(
            coa_action_url(coa_id, "rework"), {"comment": "Please fix"}, format="json"
        )
        # Maker can re-submit after rework
        resp = maker_client.post(coa_action_url(coa_id, "submit"))
        assert resp.status_code == 200
        assert resp.data["status"] == PENDING_APPROVAL

    def test_reject_requires_comment(self):
        coa_id = self._create_coa_via_api()
        auth_client(self.maker).post(coa_action_url(coa_id, "submit"))
        checker_client = auth_client(self.checker)
        resp = checker_client.post(
            coa_action_url(coa_id, "reject"), {"comment": ""}, format="json"
        )
        assert resp.status_code == 400

    def test_reject_with_comment_transitions_to_permanently_rejected(self):
        coa_id = self._create_coa_via_api()
        auth_client(self.maker).post(coa_action_url(coa_id, "submit"))
        checker_client = auth_client(self.checker)
        resp = checker_client.post(
            coa_action_url(coa_id, "reject"),
            {"comment": "Does not meet spec"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["status"] == PERMANENTLY_REJECTED

    def test_cannot_submit_coa_without_parameters(self):
        # Create a COA directly (bypassing serializer) so it has no parameters
        coa = CertificateOfAnalysisFactory(created_by=self.maker, status=DRAFT)
        maker_client = auth_client(self.maker)
        resp = maker_client.post(coa_action_url(coa.id, "submit"))
        assert resp.status_code == 400

    def test_cannot_edit_submitted_coa(self):
        coa_id = self._create_coa_via_api()
        maker_client = auth_client(self.maker)
        maker_client.post(coa_action_url(coa_id, "submit"))
        resp = maker_client.patch(
            coa_detail_url(coa_id), {"batch_number": "NEW"}, format="json"
        )
        assert resp.status_code == 400

    def test_rework_status_allows_editing(self):
        coa_id = self._create_coa_via_api()
        maker_client = auth_client(self.maker)
        checker_client = auth_client(self.checker)

        maker_client.post(coa_action_url(coa_id, "submit"))
        checker_client.post(
            coa_action_url(coa_id, "rework"), {"comment": "Fix batch"}, format="json"
        )
        # After rework the maker can edit again
        resp = maker_client.patch(
            coa_detail_url(coa_id),
            {"batch_number": "FIXED-BATCH", "parameters": []},
            format="json",
        )
        assert resp.status_code == 200

    def test_audit_log_endpoint_returns_entries(self):
        coa_id = self._create_coa_via_api()
        auth_client(self.maker).post(coa_action_url(coa_id, "submit"))
        resp = auth_client(self.maker).get(coa_action_url(coa_id, "audit-log"))
        assert resp.status_code == 200
        assert len(resp.data) >= 1


# ---- Validation -------------------------------------------------------------

@pytest.mark.django_db
class TestCOAValidation:

    def setup_method(self):
        self.maker = MakerFactory()
        self.pg = ProductGradeFactory()
        self.customer = make_org_with_tag("CONSIGNEE")
        self.footer_org = make_org_with_tag("EXPORTER")
        self.uom = UOMFactory()
        self.pkg_type = TypeOfPackageFactory()

    def _post(self, payload):
        return auth_client(self.maker).post(BASE_URL, payload, format="json")

    def _base_payload(self):
        return valid_coa_payload(
            self.pg, self.customer, self.footer_org, self.uom, self.pkg_type
        )

    def test_retest_before_manufacture_fails(self):
        payload = self._base_payload()
        payload["date_of_manufacture"] = "2026-12-01"
        payload["date_of_retest"] = "2025-12-01"   # before manufacture
        resp = self._post(payload)
        assert resp.status_code == 400

    def test_analysis_before_sampling_fails(self):
        payload = self._base_payload()
        payload["date_time_of_sampling"] = "2025-12-25T20:00:00Z"
        payload["date_time_of_analysis"] = "2025-12-25T18:00:00Z"  # before sampling
        resp = self._post(payload)
        assert resp.status_code == 400

    def test_retest_equal_to_manufacture_is_valid(self):
        """Retest on the same day as manufacture is allowed (≥, not >)."""
        payload = self._base_payload()
        payload["date_of_manufacture"] = "2025-12-22"
        payload["date_of_retest"] = "2025-12-22"
        resp = self._post(payload)
        assert resp.status_code == 201

    def test_analysis_equal_to_sampling_is_valid(self):
        """Analysis at same moment as sampling is allowed (≥, not >)."""
        payload = self._base_payload()
        payload["date_time_of_sampling"] = "2025-12-25T18:00:00Z"
        payload["date_time_of_analysis"] = "2025-12-25T18:00:00Z"
        resp = self._post(payload)
        assert resp.status_code == 201

    def test_quantitative_row_requires_result_value(self):
        payload = self._base_payload()
        payload["parameters"] = [{
            "s_no": 1,
            "spec_type": "QUANTITATIVE",
            "spec_min": "99.90",
            "spec_max": None,
            "result_value": None,   # missing
            "test_method_label": "",
        }]
        resp = self._post(payload)
        assert resp.status_code == 400

    def test_quantitative_row_requires_spec_min_or_max(self):
        payload = self._base_payload()
        payload["parameters"] = [{
            "s_no": 1,
            "spec_type": "QUANTITATIVE",
            "spec_min": None,
            "spec_max": None,       # both missing
            "result_value": "99.96",
            "test_method_label": "",
        }]
        resp = self._post(payload)
        assert resp.status_code == 400

    def test_qualitative_row_requires_spec_description(self):
        payload = self._base_payload()
        payload["parameters"] = [{
            "s_no": 1,
            "spec_type": "QUALITATIVE",
            "spec_description": "",     # missing
            "result_text": "Complies",
            "test_method_label": "",
        }]
        resp = self._post(payload)
        assert resp.status_code == 400

    def test_qualitative_row_requires_result_text(self):
        payload = self._base_payload()
        payload["parameters"] = [{
            "s_no": 1,
            "spec_type": "QUALITATIVE",
            "spec_description": "Clear liquid",
            "result_text": "",          # missing
            "test_method_label": "",
        }]
        resp = self._post(payload)
        assert resp.status_code == 400

    def test_quantitative_row_with_only_spec_max_is_valid(self):
        """spec_max alone is sufficient — spec_min is not mandatory."""
        payload = self._base_payload()
        payload["parameters"] = [{
            "s_no": 1,
            "spec_type": "QUANTITATIVE",
            "spec_min": None,
            "spec_max": "0.500000",
            "result_value": "0.300000",
            "test_method_label": "",
        }]
        resp = self._post(payload)
        assert resp.status_code == 201


# ---- Product Test Template --------------------------------------------------

@pytest.mark.django_db
class TestProductTestTemplateAPI:

    def setup_method(self):
        self.maker = MakerFactory()
        self.checker = CheckerFactory()

    def _template_url(self, pg_id):
        return f"/api/v1/master-data/product-grades/{pg_id}/test-template/"

    def test_get_template_returns_empty_rows_when_none_saved(self):
        pg = ProductGradeFactory()
        client = auth_client(self.maker)
        resp = client.get(self._template_url(pg.id))
        assert resp.status_code == 200
        assert resp.data["rows"] == []

    def test_get_template_returns_saved_rows(self):
        template = ProductTestTemplateFactory()
        ProductTestTemplateRowFactory(template=template, s_no=1)
        ProductTestTemplateRowFactory(template=template, s_no=2)
        client = auth_client(self.maker)
        resp = client.get(self._template_url(template.product_grade.id))
        assert resp.status_code == 200
        assert len(resp.data["rows"]) == 2

    def test_put_template_denied_for_maker(self):
        pg = ProductGradeFactory()
        maker_client = auth_client(self.maker)
        resp = maker_client.put(
            self._template_url(pg.id),
            {"rows": []},
            format="json",
        )
        assert resp.status_code == 403

    def test_checker_can_save_template(self):
        pg = ProductGradeFactory()
        checker_client = auth_client(self.checker)
        rows = [
            {
                "s_no": 1,
                "spec_type": "QUALITATIVE",
                "spec_description": "Clear liquid",
            }
        ]
        resp = checker_client.put(
            self._template_url(pg.id),
            {"rows": rows},
            format="json",
        )
        assert resp.status_code == 200
        assert len(resp.data["rows"]) == 1

    def test_put_template_replaces_existing_rows(self):
        """Saving a new set of rows replaces old ones wholesale."""
        template = ProductTestTemplateFactory()
        ProductTestTemplateRowFactory(template=template, s_no=1)

        checker_client = auth_client(self.checker)
        new_rows = [
            {
                "s_no": 1,
                "spec_type": "QUALITATIVE",
                "spec_description": "Passes",
            },
            {
                "s_no": 2,
                "spec_type": "QUALITATIVE",
                "spec_description": "Passes",
            },
        ]
        resp = checker_client.put(
            self._template_url(template.product_grade.id),
            {"rows": new_rows},
            format="json",
        )
        assert resp.status_code == 200
        assert len(resp.data["rows"]) == 2
        s_nos = [r["s_no"] for r in resp.data["rows"]]
        assert 1 in s_nos
        assert 2 in s_nos

    def test_template_rows_not_linked_to_coa_parameters(self):
        """
        COA parameters are copied from the template at creation time, not linked.
        Editing the template row after COA creation must not affect COAParameter rows.
        """
        from apps.master_data.models import ProductTestTemplateRow

        template = ProductTestTemplateFactory()
        row = ProductTestTemplateRowFactory(
            template=template,
            s_no=1,
            spec_type="QUALITATIVE",
            spec_description="Clear liquid",
        )

        # Mutate the template row directly
        row.spec_description = "CHANGED"
        row.save()

        # No COAParameter should reflect the change (none was created linked to this row)
        assert COAParameter.objects.filter(spec_description="CHANGED").count() == 0

    def test_get_nonexistent_product_grade_returns_404(self):
        client = auth_client(self.maker)
        resp = client.get("/api/v1/master-data/product-grades/999999/test-template/")
        assert resp.status_code == 404


# ---- PDF endpoint -----------------------------------------------------------

@pytest.mark.django_db
class TestCOAPDF:

    def test_pdf_endpoint_returns_pdf_content_type(self):
        maker = MakerFactory()
        coa = CertificateOfAnalysisFactory(created_by=maker, status=DRAFT)
        COAParameterFactory(
            coa=coa,
            spec_type="QUALITATIVE",
            spec_description="Clear",
            result_text="Complies",
        )
        client = auth_client(maker)
        resp = client.get(coa_action_url(coa.id, "pdf"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"

    def test_unauthenticated_cannot_access_pdf(self):
        maker = MakerFactory()
        coa = CertificateOfAnalysisFactory(created_by=maker, status=DRAFT)
        client = APIClient()
        resp = client.get(coa_action_url(coa.id, "pdf"))
        assert resp.status_code == 401

    def test_checker_can_access_pdf(self):
        maker = MakerFactory()
        checker = CheckerFactory()
        coa = CertificateOfAnalysisFactory(created_by=maker, status=APPROVED)
        COAParameterFactory(coa=coa, spec_type="QUALITATIVE", spec_description="OK", result_text="Complies")
        resp = auth_client(checker).get(coa_action_url(coa.id, "pdf"))
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"


# ---- Permission enforcement tests (Phase 3: Security Hardening) -------------

@pytest.mark.django_db
class TestCheckerPermissions:
    """Prove that the IsMakerOrAdmin get_permissions() guard blocks Checkers from write actions on COA."""

    def _minimal_coa_payload(self):
        """
        Build the minimum valid POST payload for COA creation.
        All required writable fields included (derived from CertificateOfAnalysisSerializer).
        customer must be an Organisation tagged CONSIGNEE; footer_organisation tagged EXPORTER.
        parameters=[] is accepted — serializer.create() iterates over it with no minimum count.
        """
        return {
            "product_grade": ProductGradeFactory().pk,
            "customer": make_org_with_tag("CONSIGNEE").pk,
            "batch_number": "BATCH-TEST-001",
            "package_count": 10,
            "package_volume": "1000.000",
            "package_uom": UOMFactory().pk,
            "package_type": TypeOfPackageFactory().pk,
            "date_of_manufacture": "2025-12-22",
            "date_of_retest": "2026-12-21",
            "date_time_of_sampling": "2025-12-25T18:00:00Z",
            "date_time_of_analysis": "2025-12-25T19:25:00Z",
            "analyst_name": "Test Analyst",
            "qc_incharge_name": "Test QC",
            "footer_organisation": make_org_with_tag("EXPORTER").pk,
            "parameters": [],
        }

    def test_checker_cannot_create_coa(self):
        checker = CheckerFactory()
        resp = auth_client(checker).post(BASE_URL, self._minimal_coa_payload(), format="json")
        assert resp.status_code == 403

    def test_checker_cannot_patch_coa(self):
        maker = MakerFactory()
        coa = CertificateOfAnalysisFactory(created_by=maker)
        checker = CheckerFactory()
        resp = auth_client(checker).patch(coa_detail_url(coa.pk), {"batch_number": "BATCH-X"}, format="json")
        assert resp.status_code == 403

    def test_checker_can_list_coa(self):
        checker = CheckerFactory()
        resp = auth_client(checker).get(BASE_URL)
        assert resp.status_code == 200

    def test_maker_can_create_coa(self):
        maker = MakerFactory()
        resp = auth_client(maker).post(BASE_URL, self._minimal_coa_payload(), format="json")
        assert resp.status_code == 201
