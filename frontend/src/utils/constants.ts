// Mirror of backend enums. Import from here — never hardcode these strings in components.
// Constraint #23: status values and role constants must come from this file.

export const ROLES = {
  COMPANY_ADMIN: "COMPANY_ADMIN",
  CHECKER: "CHECKER",
  MAKER: "MAKER",
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];

export const DOCUMENT_STATUS = {
  DRAFT: "DRAFT",
  PENDING_APPROVAL: "PENDING_APPROVAL",
  APPROVED: "APPROVED",
  REWORK: "REWORK",
  REJECTED: "REJECTED",
  PERMANENTLY_REJECTED: "PERMANENTLY_REJECTED",
  DISABLED: "DISABLED",
} as const;

export type DocumentStatus = (typeof DOCUMENT_STATUS)[keyof typeof DOCUMENT_STATUS];

export const ORG_TAGS = {
  EXPORTER: "EXPORTER",
  CONSIGNEE: "CONSIGNEE",
  BUYER: "BUYER",
  NOTIFY_PARTY: "NOTIFY_PARTY",
} as const;

export type OrgTag = (typeof ORG_TAGS)[keyof typeof ORG_TAGS];

export const ORG_TAG_LABELS: Record<OrgTag, string> = {
  EXPORTER: "Exporter",
  CONSIGNEE: "Consignee",
  BUYER: "Buyer",
  NOTIFY_PARTY: "Notify Party",
};

export const ADDRESS_TYPES = {
  REGISTERED: "REGISTERED",
  FACTORY: "FACTORY",
  OFFICE: "OFFICE",
} as const;

export type AddressType = (typeof ADDRESS_TYPES)[keyof typeof ADDRESS_TYPES];

export const ADDRESS_TYPE_LABELS: Record<AddressType, string> = {
  REGISTERED: "Registered",
  FACTORY: "Factory",
  OFFICE: "Office",
};
