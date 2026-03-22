import { Routes, Route, Navigate } from "react-router-dom";

import LoginPage from "./pages/auth/LoginPage";
import DashboardPage from "./pages/dashboard/DashboardPage";
import OrganisationListPage from "./pages/master-data/OrganisationListPage";
import OrganisationFormPage from "./pages/master-data/OrganisationFormPage";
import BankListPage from "./pages/master-data/BankListPage";
import BankFormPage from "./pages/master-data/BankFormPage";
import TCTemplateListPage from "./pages/master-data/TCTemplateListPage";
import TCTemplateFormPage from "./pages/master-data/TCTemplateFormPage";
import UserListPage from "./pages/users/UserListPage";
import ReferenceDataPage from "./pages/master-data/ReferenceDataPage";

import ProformaInvoiceListPage from "./pages/proforma-invoice/ProformaInvoiceListPage";
import ProformaInvoiceCreatePage from "./pages/proforma-invoice/ProformaInvoiceCreatePage";
import ProformaInvoiceDetailPage from "./pages/proforma-invoice/ProformaInvoiceDetailPage";
import ProformaInvoiceEditPage from "./pages/proforma-invoice/ProformaInvoiceEditPage";

import PackingListListPage from "./pages/packing-list/PackingListListPage";
import PackingListCreatePage from "./pages/packing-list/PackingListCreatePage";
import PackingListDetailPage from "./pages/packing-list/PackingListDetailPage";
import PackingListEditPage from "./pages/packing-list/PackingListEditPage";

import PurchaseOrderListPage from "./pages/purchase-order/PurchaseOrderListPage";
import PurchaseOrderFormPage from "./pages/purchase-order/PurchaseOrderFormPage";
import PurchaseOrderDetailPage from "./pages/purchase-order/PurchaseOrderDetailPage";

import ReportsPage from "./pages/reports/ReportsPage";

import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import { ROLES } from "./utils/constants";

export default function App() {
  return (
    <Routes>
      {/* Public route — accessible without login */}
      <Route path="/login" element={<LoginPage />} />

      {/* All routes below require authentication and render inside the sidebar layout */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />

        {/* Master data — Checker and Company Admin only */}
        <Route
          path="/master-data/organisations"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <OrganisationListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/master-data/organisations/new"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <OrganisationFormPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/master-data/organisations/:id/edit"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <OrganisationFormPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/master-data/banks"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <BankListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/master-data/banks/new"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <BankFormPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/master-data/banks/:id/edit"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <BankFormPage />
            </ProtectedRoute>
          }
        />
        {/* T&C Templates — Checker and Company Admin can write; all roles can read */}
        <Route
          path="/master-data/tc-templates"
          element={<TCTemplateListPage />}
        />
        <Route
          path="/master-data/tc-templates/new"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <TCTemplateFormPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/master-data/tc-templates/:id/edit"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <TCTemplateFormPage />
            </ProtectedRoute>
          }
        />

        {/* Reference Data — readable by all, writable by Checker/Admin */}
        <Route path="/master-data/reference-data" element={<ReferenceDataPage />} />

        {/* Proforma Invoice — all roles can read; Maker can create/edit */}
        <Route path="/proforma-invoices" element={<ProformaInvoiceListPage />} />
        <Route
          path="/proforma-invoices/new"
          element={
            <ProtectedRoute allowedRoles={[ROLES.MAKER, ROLES.COMPANY_ADMIN]}>
              <ProformaInvoiceCreatePage />
            </ProtectedRoute>
          }
        />
        <Route path="/proforma-invoices/:id" element={<ProformaInvoiceDetailPage />} />
        <Route
          path="/proforma-invoices/:id/edit"
          element={
            <ProtectedRoute allowedRoles={[ROLES.MAKER, ROLES.COMPANY_ADMIN]}>
              <ProformaInvoiceEditPage />
            </ProtectedRoute>
          }
        />

        {/* Packing List — all roles can read; Maker/Admin can create/edit */}
        <Route path="/packing-lists" element={<PackingListListPage />} />
        <Route
          path="/packing-lists/new"
          element={
            <ProtectedRoute allowedRoles={[ROLES.MAKER, ROLES.COMPANY_ADMIN]}>
              <PackingListCreatePage />
            </ProtectedRoute>
          }
        />
        <Route path="/packing-lists/:id" element={<PackingListDetailPage />} />
        <Route
          path="/packing-lists/:id/edit"
          element={
            <ProtectedRoute allowedRoles={[ROLES.MAKER, ROLES.COMPANY_ADMIN]}>
              <PackingListCreatePage />
            </ProtectedRoute>
          }
        />

        {/* Purchase Orders — all roles */}
        <Route path="/purchase-orders" element={<PurchaseOrderListPage />} />
        <Route path="/purchase-orders/new" element={<PurchaseOrderFormPage />} />
        <Route path="/purchase-orders/:id" element={<PurchaseOrderDetailPage />} />
        <Route path="/purchase-orders/:id/edit" element={<PurchaseOrderFormPage />} />

        {/* User Management — Company Admin only */}
        <Route
          path="/users"
          element={
            <ProtectedRoute allowedRoles={[ROLES.COMPANY_ADMIN]}>
              <UserListPage />
            </ProtectedRoute>
          }
        />

        {/* Reports — Checker and Company Admin only */}
        <Route
          path="/reports"
          element={
            <ProtectedRoute allowedRoles={[ROLES.CHECKER, ROLES.COMPANY_ADMIN]}>
              <ReportsPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch-all: redirect unknown URLs to dashboard */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
