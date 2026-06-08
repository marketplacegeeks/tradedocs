// All COA (Certificate of Analysis) API calls.
// Constraint #22: no component calls axios directly — only api files do.

import axiosInstance from "./axiosInstance";

// ---- COA types --------------------------------------------------------------

export interface COAParameter {
  id?: number;
  s_no: number;
  parameter?: number | null;
  parameter_name?: string | null;
  unit?: number | null;
  unit_abbreviation?: string | null;
  spec_type: "QUANTITATIVE" | "QUALITATIVE";
  spec_min?: string | null;
  spec_max?: string | null;
  spec_description?: string;
  result_value?: string | null;
  result_text?: string;
  test_method?: number | null;
  test_method_code?: string | null;
}

export interface COA {
  id: number;
  coa_number: string;
  product_grade: number;
  product_name: string;
  grade: string;
  customer: number;
  customer_name: string;
  batch_number: string;
  package_count: number;
  package_volume: string;
  package_uom: number;
  package_uom_abbreviation: string;
  package_type: number;
  package_type_name: string;
  date_of_despatch?: string | null;
  date_of_manufacture: string;
  date_of_retest: string;
  date_time_of_sampling: string;
  date_time_of_analysis: string;
  analyst_name: string;
  qc_incharge_name: string;
  footer_organisation: number;
  footer_organisation_name: string;
  status: string;
  created_by: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  parameters: COAParameter[];
}

// Payload excludes all read-only fields that the server sets automatically.
export type COAPayload = Omit<
  COA,
  | "id"
  | "coa_number"
  | "status"
  | "created_by"
  | "created_by_name"
  | "created_at"
  | "updated_at"
  | "product_name"
  | "grade"
  | "customer_name"
  | "package_uom_abbreviation"
  | "package_type_name"
  | "footer_organisation_name"
>;

// ---- Master data types for COA dropdowns ------------------------------------

export interface Product {
  id: number;
  name: string;
  cas_number: string;
  is_active: boolean;
  grades: ProductGrade[];
}

export interface ProductGrade {
  id: number;
  product: number;
  grade: string;
  is_active: boolean;
}

export interface TestParameter {
  id: number;
  name: string;
  default_unit: number | null;
  default_unit_abbreviation: string | null;
  default_test_method: number | null;
  default_test_method_code: string | null;
  is_active: boolean;
}

export interface TestMethod {
  id: number;
  code: string;
  description: string;
  is_active: boolean;
}

// ---- COA CRUD & workflow -----------------------------------------------------

export const listCOAs = (params?: Record<string, string>) =>
  axiosInstance.get<COA[]>("/coas/", { params });

export const getCOA = (id: number) =>
  axiosInstance.get<COA>(`/coas/${id}/`);

export const createCOA = (data: COAPayload) =>
  axiosInstance.post<COA>("/coas/", data);

export const updateCOA = (id: number, data: Partial<COAPayload>) =>
  axiosInstance.patch<COA>(`/coas/${id}/`, data);

export const submitCOA = (id: number) =>
  axiosInstance.post<{ status: string }>(`/coas/${id}/submit/`);

export const approveCOA = (id: number) =>
  axiosInstance.post<{ status: string }>(`/coas/${id}/approve/`);

export const rejectCOA = (id: number, comment: string) =>
  axiosInstance.post<{ status: string }>(`/coas/${id}/reject/`, { comment });

export const reworkCOA = (id: number, comment: string) =>
  axiosInstance.post<{ status: string }>(`/coas/${id}/rework/`, { comment });

export const getCOAPdf = (id: number) =>
  axiosInstance.get(`/coas/${id}/pdf/`, { responseType: "blob" });

export const getCOAAuditLog = (id: number) =>
  axiosInstance.get(`/coas/${id}/audit-log/`);

// ---- Product grade test template --------------------------------------------

export const getProductGradeTemplate = (productGradeId: number) =>
  axiosInstance.get(`/master-data/product-grades/${productGradeId}/test-template/`);

export const saveProductGradeTemplate = (productGradeId: number, rows: COAParameter[]) =>
  axiosInstance.put(`/master-data/product-grades/${productGradeId}/test-template/`, { rows });

// ---- Product master data ----------------------------------------------------

export const listProducts = (params?: Record<string, string>) =>
  axiosInstance.get<Product[]>("/master-data/products/", { params });

export const createProduct = (data: { name: string; cas_number?: string }) =>
  axiosInstance.post<Product>("/master-data/products/", data);

export const updateProduct = (id: number, data: { name?: string; cas_number?: string; is_active?: boolean }) =>
  axiosInstance.patch<Product>(`/master-data/products/${id}/`, data);

export const deleteProduct = (id: number) =>
  axiosInstance.delete(`/master-data/products/${id}/`);

export const listProductGrades = (productId: number) =>
  axiosInstance.get<ProductGrade[]>(`/master-data/products/${productId}/grades/`);

export const createProductGrade = (productId: number, data: { grade: string }) =>
  axiosInstance.post<ProductGrade>(`/master-data/products/${productId}/grades/`, data);

export const updateProductGrade = (productId: number, gradeId: number, data: { grade?: string; is_active?: boolean }) =>
  axiosInstance.patch<ProductGrade>(`/master-data/products/${productId}/grades/${gradeId}/`, data);

// ---- Test parameter master data ---------------------------------------------

export const listTestParameters = (params?: Record<string, string>) =>
  axiosInstance.get<TestParameter[]>("/master-data/test-parameters/", { params });

export const createTestParameter = (data: { name: string; default_unit?: number | null; default_test_method?: number | null }) =>
  axiosInstance.post<TestParameter>("/master-data/test-parameters/", data);

export const updateTestParameter = (id: number, data: { name?: string; default_unit?: number | null; default_test_method?: number | null; is_active?: boolean }) =>
  axiosInstance.patch<TestParameter>(`/master-data/test-parameters/${id}/`, data);

export const deleteTestParameter = (id: number) =>
  axiosInstance.delete(`/master-data/test-parameters/${id}/`);

// ---- Test method master data ------------------------------------------------

export const listTestMethods = (params?: Record<string, string>) =>
  axiosInstance.get<TestMethod[]>("/master-data/test-methods/", { params });

export const createTestMethod = (data: { code: string; description?: string }) =>
  axiosInstance.post<TestMethod>("/master-data/test-methods/", data);

export const updateTestMethod = (id: number, data: { code?: string; description?: string; is_active?: boolean }) =>
  axiosInstance.patch<TestMethod>(`/master-data/test-methods/${id}/`, data);

export const deleteTestMethod = (id: number) =>
  axiosInstance.delete(`/master-data/test-methods/${id}/`);
