// Bank accounts list page — design system table layout.

import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Search, ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";
import { message } from "antd";

import { listBanks, deactivateBank, deleteBank } from "../../api/banks";
import type { Bank } from "../../api/banks";
import { extractApiError } from "../../utils/apiErrors";
import { useAuth } from "../../store/AuthContext";
import { ROLES, ACCOUNT_TYPE_LABELS } from "../../utils/constants";
import type { AccountType } from "../../utils/constants";

const ACCOUNT_TYPE_CHIP: Record<string, string> = {
  CURRENT: "chip-blue",
  SAVINGS: "chip-green",
  CHECKING: "chip-purple",
};

type SortKey = "nickname" | "bank_name" | "currency_code";
type SortDir = "asc" | "desc" | null;
type SortConfig = { key: SortKey; dir: SortDir } | null;

export default function BankListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canWrite = user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN || user?.role === ROLES.SUPER_ADMIN;

  const [searchQuery, setSearchQuery] = useState("");
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);

  const { data: banks = [], isLoading } = useQuery({
    queryKey: ["banks"],
    queryFn: listBanks,
  });

  // Filter by nickname or bank name, then sort
  const displayed = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    let rows = q
      ? banks.filter(
          (b: Bank) =>
            b.nickname.toLowerCase().includes(q) ||
            b.bank_name.toLowerCase().includes(q)
        )
      : banks;
    if (sortConfig?.dir) {
      rows = [...rows].sort((a, b) => {
        const av = String(a[sortConfig.key] ?? "").toLowerCase();
        const bv = String(b[sortConfig.key] ?? "").toLowerCase();
        return sortConfig.dir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      });
    }
    return rows;
  }, [banks, searchQuery, sortConfig]);

  // Cycle: null → asc → desc → null
  function toggleSort(key: SortKey) {
    setSortConfig((prev) => {
      if (!prev || prev.key !== key) return { key, dir: "asc" };
      if (prev.dir === "asc") return { key, dir: "desc" };
      return null;
    });
  }

  function sortIcon(key: SortKey) {
    if (!sortConfig || sortConfig.key !== key) {
      return <ChevronsUpDown size={12} strokeWidth={1.5} color="var(--text-muted)" />;
    }
    return sortConfig.dir === "asc"
      ? <ChevronUp size={12} strokeWidth={2} color="var(--primary)" />
      : <ChevronDown size={12} strokeWidth={2} color="var(--primary)" />;
  }

  function sortHeaderStyle(key: SortKey): React.CSSProperties {
    return {
      padding: "12px 16px",
      textAlign: "left",
      fontFamily: "var(--font-body)",
      fontSize: 11,
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: "0.06em",
      color: sortConfig?.key === key ? "var(--primary)" : "var(--text-muted)",
      borderBottom: "1px solid var(--border-light)",
      whiteSpace: "nowrap",
      cursor: "pointer",
      userSelect: "none",
    };
  }

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

  const isSuperAdmin = user?.role === ROLES.SUPER_ADMIN;

  const hardDeleteMutation = useMutation({
    mutationFn: (id: number) => deleteBank(id),
    onSuccess: () => {
      message.success("Bank account permanently deleted.");
      queryClient.invalidateQueries({ queryKey: ["banks"] });
    },
    onError: (err: unknown) => message.error(extractApiError(err, "Delete failed. Please try again.")),
  });

  function handleHardDelete(bank: Bank) {
    if (window.confirm(`Permanently delete "${bank.nickname}"? This cannot be undone.`)) {
      hardDeleteMutation.mutate(bank.id);
    }
  }

  const countLabel = searchQuery.trim()
    ? `${displayed.length} of ${banks.length} account${banks.length !== 1 ? "s" : ""}`
    : `${banks.length} account${banks.length !== 1 ? "s" : ""} registered`;

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
            {countLabel}
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

      {/* Search bar */}
      <div style={{ position: "relative", marginBottom: 16 }}>
        <Search
          size={15}
          strokeWidth={1.5}
          style={{
            position: "absolute",
            left: 12,
            top: "50%",
            transform: "translateY(-50%)",
            color: "var(--text-muted)",
            pointerEvents: "none",
          }}
        />
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by nickname or bank name…"
          style={{
            width: "100%",
            padding: "9px 14px 9px 36px",
            background: "var(--bg-input)",
            border: "1px solid var(--border-medium)",
            borderRadius: 8,
            fontFamily: "var(--font-body)",
            fontSize: 14,
            color: "var(--text-primary)",
            outline: "none",
            boxSizing: "border-box",
            transition: "border-color 0.15s ease",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--primary)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-medium)")}
        />
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
        ) : displayed.length === 0 ? (
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
              {searchQuery.trim() ? `No results for "${searchQuery.trim()}"` : "No bank accounts yet"}
            </p>
            <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
              {searchQuery.trim()
                ? "Try a different search term."
                : canWrite
                ? 'Click "New Bank Account" to add one.'
                : "No bank accounts have been added."}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <th onClick={() => toggleSort("nickname")} style={sortHeaderStyle("nickname")}>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      Nickname {sortIcon("nickname")}
                    </div>
                  </th>
                  <th onClick={() => toggleSort("bank_name")} style={sortHeaderStyle("bank_name")}>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      Bank Name {sortIcon("bank_name")}
                    </div>
                  </th>
                  {["Account Number", "Type"].map((h) => (
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
                  <th onClick={() => toggleSort("currency_code")} style={sortHeaderStyle("currency_code")}>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      Currency {sortIcon("currency_code")}
                    </div>
                  </th>
                  {["Country", "SWIFT"].map((h) => (
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
                {displayed.map((bank: Bank) => (
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
                          {isSuperAdmin && (
                            <button
                              onClick={() => handleHardDelete(bank)}
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: 4,
                                padding: "5px 10px",
                                background: "transparent",
                                border: "1px solid var(--error)",
                                borderRadius: 6,
                                fontFamily: "var(--font-body)",
                                fontSize: 12,
                                fontWeight: 500,
                                color: "var(--error)",
                                cursor: "pointer",
                              }}
                              onMouseEnter={(e) =>
                                ((e.currentTarget as HTMLButtonElement).style.background = "#fff0f0")
                              }
                              onMouseLeave={(e) =>
                                ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
                              }
                            >
                              <Trash2 size={12} strokeWidth={1.5} />
                              Delete
                            </button>
                          )}
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
