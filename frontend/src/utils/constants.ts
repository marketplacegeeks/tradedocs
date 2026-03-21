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
  VENDOR: "VENDOR",
} as const;

export type OrgTag = (typeof ORG_TAGS)[keyof typeof ORG_TAGS];

export const ORG_TAG_LABELS: Record<OrgTag, string> = {
  EXPORTER: "Exporter",
  CONSIGNEE: "Consignee",
  BUYER: "Buyer",
  NOTIFY_PARTY: "Notify Party",
  VENDOR: "Vendor",
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
  OFFICE: "Corporate Office",
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

// ISO 3166-1 Alpha-2 → E.164 dial code.
// Used by the Organisation form to auto-fill the Phone Dial Code when a country is selected.
export const COUNTRY_DIAL_CODES: Record<string, string> = {
  AF: "+93", AL: "+355", DZ: "+213", AD: "+376", AO: "+244", AG: "+1-268",
  AR: "+54", AM: "+374", AU: "+61", AT: "+43", AZ: "+994", BS: "+1-242",
  BH: "+973", BD: "+880", BB: "+1-246", BY: "+375", BE: "+32", BZ: "+501",
  BJ: "+229", BT: "+975", BO: "+591", BA: "+387", BW: "+267", BR: "+55",
  BN: "+673", BG: "+359", BF: "+226", BI: "+257", CV: "+238", KH: "+855",
  CM: "+237", CA: "+1", CF: "+236", TD: "+235", CL: "+56", CN: "+86",
  CO: "+57", KM: "+269", CG: "+242", CD: "+243", CR: "+506", HR: "+385",
  CU: "+53", CY: "+357", CZ: "+420", DK: "+45", DJ: "+253", DM: "+1-767",
  DO: "+1-809", EC: "+593", EG: "+20", SV: "+503", GQ: "+240", ER: "+291",
  EE: "+372", SZ: "+268", ET: "+251", FJ: "+679", FI: "+358", FR: "+33",
  GA: "+241", GM: "+220", GE: "+995", DE: "+49", GH: "+233", GR: "+30",
  GD: "+1-473", GT: "+502", GN: "+224", GW: "+245", GY: "+592", HT: "+509",
  HN: "+504", HU: "+36", IS: "+354", IN: "+91", ID: "+62", IR: "+98",
  IQ: "+964", IE: "+353", IL: "+972", IT: "+39", JM: "+1-876", JP: "+81",
  JO: "+962", KZ: "+7", KE: "+254", KI: "+686", KP: "+850", KR: "+82",
  KW: "+965", KG: "+996", LA: "+856", LV: "+371", LB: "+961", LS: "+266",
  LR: "+231", LY: "+218", LI: "+423", LT: "+370", LU: "+352", MG: "+261",
  MW: "+265", MY: "+60", MV: "+960", ML: "+223", MT: "+356", MH: "+692",
  MR: "+222", MU: "+230", MX: "+52", FM: "+691", MD: "+373", MC: "+377",
  MN: "+976", ME: "+382", MA: "+212", MZ: "+258", MM: "+95", NA: "+264",
  NR: "+674", NP: "+977", NL: "+31", NZ: "+64", NI: "+505", NE: "+227",
  NG: "+234", NO: "+47", OM: "+968", PK: "+92", PW: "+680", PA: "+507",
  PG: "+675", PY: "+595", PE: "+51", PH: "+63", PL: "+48", PT: "+351",
  QA: "+974", RO: "+40", RU: "+7", RW: "+250", KN: "+1-869", LC: "+1-758",
  VC: "+1-784", WS: "+685", SM: "+378", ST: "+239", SA: "+966", SN: "+221",
  RS: "+381", SC: "+248", SL: "+232", SG: "+65", SK: "+421", SI: "+386",
  SB: "+677", SO: "+252", ZA: "+27", SS: "+211", ES: "+34", LK: "+94",
  SD: "+249", SR: "+597", SE: "+46", CH: "+41", SY: "+963", TW: "+886",
  TJ: "+992", TZ: "+255", TH: "+66", TL: "+670", TG: "+228", TO: "+676",
  TT: "+1-868", TN: "+216", TR: "+90", TM: "+993", TV: "+688", UG: "+256",
  UA: "+380", AE: "+971", GB: "+44", US: "+1", UY: "+598", UZ: "+998",
  VU: "+678", VE: "+58", VN: "+84", YE: "+967", ZM: "+260", ZW: "+263",
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

// Human-readable labels for workflow action strings (as stored in AuditLog.action).
export const WORKFLOW_ACTION_LABELS: Record<string, string> = {
  SUBMIT: "Submitted",
  APPROVE: "Approved",
  REWORK: "Sent for Rework",
  PERMANENTLY_REJECT: "Permanently Rejected",
};
