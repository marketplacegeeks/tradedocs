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
  PERMANENTLY_REJECTED: "PERMANENTLY_REJECTED",
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

export const ACCOUNT_TYPES = {
  CURRENT: "CURRENT",
  SAVINGS: "SAVINGS",
  CHECKING: "CHECKING",
} as const;

export type AccountType = (typeof ACCOUNT_TYPES)[keyof typeof ACCOUNT_TYPES];

export const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  CURRENT: "Current",
  SAVINGS: "Savings",
  CHECKING: "Checking",
};

export const SHIPMENT_OPTIONS = {
  ALLOWED: "ALLOWED",
  NOT_ALLOWED: "NOT_ALLOWED",
} as const;

export type ShipmentOption = (typeof SHIPMENT_OPTIONS)[keyof typeof SHIPMENT_OPTIONS];

export const SHIPMENT_OPTION_LABELS: Record<ShipmentOption, string> = {
  ALLOWED: "Allowed",
  NOT_ALLOWED: "Not Allowed",
};

// Maps incoterm code → set of cost fields the seller pays (and must fill in on the PI form).
// Used by the PI form and detail page to conditionally show/hide the cost breakdown section.
export const INCOTERM_SELLER_FIELDS: Record<string, Set<string>> = {
  EXW: new Set(),
  FCA: new Set(),                                                    // FOB Value only; buyer bears freight
  FOB: new Set(),                                                    // FOB Value only; buyer bears freight
  CFR: new Set(["freight"]),                                         // seller pays freight only
  CIF: new Set(["freight", "insurance_amount"]),
  CPT: new Set(["freight"]),                                         // seller pays freight only
  CIP: new Set(["freight", "insurance_amount"]),
  DAP: new Set(["freight", "insurance_amount"]),
  DPU: new Set(["freight", "insurance_amount", "destination_charges"]),
  DDP: new Set(["freight", "insurance_amount", "import_duty", "destination_charges"]),
};

// Maps incoterm code → which of the PL/CI cost fields the seller must fill in.
// Used by the PL creation wizard (Step 5) and Edit page to show/hide FOB Rate, Freight, Insurance.
// FR-14M.8B: L/C Details is always shown and is NOT in these sets.
export const INCOTERM_PL_FIELDS: Record<string, Set<string>> = {
  EXW: new Set(),
  FCA: new Set(["fob_rate"]),
  FOB: new Set(["fob_rate"]),
  CFR: new Set(["fob_rate", "freight"]),
  CIF: new Set(["fob_rate", "freight", "insurance"]),
  CPT: new Set(["fob_rate", "freight"]),
  CIP: new Set(["fob_rate", "freight", "insurance"]),
  DAP: new Set(["fob_rate", "freight", "insurance"]),
  DPU: new Set(["fob_rate", "freight", "insurance"]),
  DDP: new Set(["fob_rate", "freight", "insurance"]),
};

// Human-readable labels for PI cost breakdown fields
export const COST_FIELD_LABELS: Record<string, string> = {
  freight: "Freight",
  insurance_amount: "Insurance Amount",
  import_duty: "Import Duty / Taxes",
  destination_charges: "Destination Charges",
};

// Status label + chip color mappings for the PI list
export const DOCUMENT_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  PENDING_APPROVAL: "Pending Approval",
  APPROVED: "Approved",
  REWORK: "Rework",
  PERMANENTLY_REJECTED: "Permanently Rejected",
};

export const DOCUMENT_STATUS_CHIP: Record<string, string> = {
  DRAFT: "chip-blue",
  PENDING_APPROVAL: "chip-yellow",
  APPROVED: "chip-green",
  REWORK: "chip-orange",
  PERMANENTLY_REJECTED: "chip-pink",
};
