// Bank accounts list page — design system table layout.

import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { message } from "antd";

import { listBanks, deactivateBank } from "../../api/banks";
import type { Bank } from "../../api/banks";
import { useAuth } from "../../store/AuthContext";
import { ROLES, ACCOUNT_TYPE_LABELS } from "../../utils/constants";
import type { AccountType } from "../../utils/constants";

const ACCOUNT_TYPE_CHIP: Record<string, string> = {
  CURRENT: "chip-blue",
  SAVINGS: "chip-green",
  CHECKING: "chip-purple",
};

export default function BankListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canWrite = user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN;

  const { data: banks = [], isLoading } = useQuery({
    queryKey: ["banks"],
    queryFn: listBanks,
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => deactivateBank(id),
    onSuccess: () => {
      message.success("Bank account deactivated.");
      queryClient.invalidateQueries({ queryKey: ["banks"] });
    },
    onError: () => {
      message.error("Failed to deactivate bank account.");
    },
  });

  function handleDeactivate(bank: Bank) {
    if (window.confirm(`Deactivate "${bank.nickname}"? It will no longer appear in document dropdowns.`)) {
      deactivateMutation.mutate(bank.id);
    }
  }

  return (
    <div>
      {/* Page header */}
      <div
        className="page-header"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: 22,
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            Bank Accounts
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {banks.length} account{banks.length !== 1 ? "s" : ""} registered
          </p>
        </div>
        {canWrite && (
          <button
            onClick={() => navigate("/master-data/banks/new")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "9px 16px",
              background: "var(--primary)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontFamily: "var(--font-body)",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "var(--primary-hover)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "var(--primary)")
            }
          >
            <Plus size={16} strokeWidth={2} />
            New Bank Account
          </button>
        )}
      </div>

      {/* Table card */}
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-light)",
          borderRadius: 14,
          boxShadow: "var(--shadow-card)",
          overflow: "hidden",
        }}
      >
        {isLoading ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-body)" }}>
            Loading…
          </div>
        ) : banks.length === 0 ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              padding: "48px 24px",
              gap: 12,
            }}
          >
            <p style={{ fontFamily: "var(--font-heading)", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              No bank accounts yet
            </p>
            <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
              {canWrite ? "Click \"New Bank Account\" to add one." : "No bank accounts have been added."}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  {["Nickname", "Bank Name", "Account Number", "Type", "Currency", "Country", "SWIFT"].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "12px 16px",
                        textAlign: "left",
                        fontFamily: "var(--font-body)",
                        fontSize: 11,
                        fontWeight: 600,
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        color: "var(--text-muted)",
                        borderBottom: "1px solid var(--border-light)",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                  {canWrite && (
                    <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                  )}
                </tr>
              </thead>
              <tbody>
                {banks.map((bank: Bank) => (
                  <tr
                    key={bank.id}
                    style={{ cursor: "default" }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLTableRowElement).style.background = "transparent";
                    }}
                  >
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)" }}>
                      <span style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>
                        {bank.nickname}
                      </span>
                    </td>
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)", fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-secondary)" }}>
                      {bank.bank_name}
                    </td>
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)", fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                      {bank.account_number}
                    </td>
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)" }}>
                      <span className={`chip ${ACCOUNT_TYPE_CHIP[bank.account_type] ?? "chip-blue"}`}>
                        {ACCOUNT_TYPE_LABELS[bank.account_type as AccountType] ?? bank.account_type}
                      </span>
                    </td>
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)" }}>
                      <span className="chip chip-green">{bank.currency_code}</span>
                    </td>
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)", fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-secondary)" }}>
                      {bank.bank_country_name}
                    </td>
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)", fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>
                      {bank.swift_code || "—"}
                    </td>
                    {canWrite && (
                      <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)", textAlign: "right" }}>
                        <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                          <button
                            onClick={() => navigate(`/master-data/banks/${bank.id}/edit`)}
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 4,
                              padding: "5px 10px",
                              background: "transparent",
                              border: "1px solid var(--border-medium)",
                              borderRadius: 6,
                              fontFamily: "var(--font-body)",
                              fontSize: 12,
                              fontWeight: 500,
                              color: "var(--text-secondary)",
                              cursor: "pointer",
                            }}
                            onMouseEnter={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)")
                            }
                            onMouseLeave={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
                            }
                          >
                            <Pencil size={12} strokeWidth={1.5} />
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeactivate(bank)}
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 4,
                              padding: "5px 10px",
                              background: "transparent",
                              border: "1px solid var(--pastel-pink-text)",
                              borderRadius: 6,
                              fontFamily: "var(--font-body)",
                              fontSize: 12,
                              fontWeight: 500,
                              color: "var(--pastel-pink-text)",
                              cursor: "pointer",
                            }}
                            onMouseEnter={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background = "var(--pastel-pink)")
                            }
                            onMouseLeave={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
                            }
                          >
                            <Trash2 size={12} strokeWidth={1.5} />
                            Deactivate
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
