// Organisation list page — design system table layout.
// Checker and Company Admin can create / deactivate. Makers can only view.

import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Search, ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";
import { message } from "antd";

import { listOrganisations, updateOrganisation, deleteOrganisation } from "../../api/organisations";
import type { Organisation } from "../../api/organisations";
import { extractApiError } from "../../utils/apiErrors";
import { useAuth } from "../../store/AuthContext";
import { ROLES, ORG_TAG_LABELS } from "../../utils/constants";
import type { OrgTag } from "../../utils/constants";

// Pastel chip class per organisation type tag
const TAG_CHIP: Record<string, string> = {
  EXPORTER: "chip-blue",
  CONSIGNEE: "chip-green",
  BUYER: "chip-orange",
  NOTIFY_PARTY: "chip-purple",
  VENDOR: "chip-yellow",
};

type SortDir = "asc" | "desc" | null;

export default function OrganisationListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canWrite = user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN || user?.role === ROLES.SUPER_ADMIN;

  const [searchQuery, setSearchQuery] = useState("");
  const [sortDir, setSortDir] = useState<SortDir>(null);

  const { data: organisations = [], isLoading } = useQuery({
    queryKey: ["organisations"],
    queryFn: () => listOrganisations(),
  });

  // Filter by name, then sort
  const displayed = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    let rows = q
      ? organisations.filter((o: Organisation) => o.name.toLowerCase().includes(q))
      : organisations;
    if (sortDir) {
      rows = [...rows].sort((a, b) =>
        sortDir === "asc"
          ? a.name.localeCompare(b.name)
          : b.name.localeCompare(a.name)
      );
    }
    return rows;
  }, [organisations, searchQuery, sortDir]);

  function toggleSort() {
    setSortDir((prev) => (prev === null ? "asc" : prev === "asc" ? "desc" : null));
  }

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => updateOrganisation(id, { is_active: false }),
    onSuccess: () => {
      message.success("Organisation deactivated.");
      queryClient.invalidateQueries({ queryKey: ["organisations"] });
    },
    onError: () => {
      message.error("Failed to deactivate organisation.");
    },
  });

  function handleDeactivate(org: Organisation) {
    if (window.confirm(`Deactivate "${org.name}"? It will no longer appear in document dropdowns.`)) {
      deactivateMutation.mutate(org.id);
    }
  }

  const isSuperAdmin = user?.role === ROLES.SUPER_ADMIN;

  const hardDeleteMutation = useMutation({
    mutationFn: (id: number) => deleteOrganisation(id),
    onSuccess: () => {
      message.success("Organisation permanently deleted.");
      queryClient.invalidateQueries({ queryKey: ["organisations"] });
    },
    onError: (err: unknown) => message.error(extractApiError(err, "Delete failed. Please try again.")),
  });

  function handleHardDelete(org: Organisation) {
    if (window.confirm(`Permanently delete "${org.name}"? This cannot be undone.`)) {
      hardDeleteMutation.mutate(org.id);
    }
  }

  const countLabel = searchQuery.trim()
    ? `${displayed.length} of ${organisations.length} organisation${organisations.length !== 1 ? "s" : ""}`
    : `${organisations.length} organisation${organisations.length !== 1 ? "s" : ""} registered`;

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
            Organisations
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {countLabel}
          </p>
        </div>
        {canWrite && (
          <button
            onClick={() => navigate("/master-data/organisations/new")}
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
            New Organisation
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
          placeholder="Search organisations…"
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
              {searchQuery.trim() ? `No results for "${searchQuery.trim()}"` : "No organisations yet"}
            </p>
            <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
              {searchQuery.trim()
                ? "Try a different search term."
                : canWrite
                ? 'Click "New Organisation" to add one.'
                : "No organisations have been added."}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 640 }}>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  {/* Sortable Name column */}
                  <th
                    onClick={toggleSort}
                    style={{
                      padding: "12px 16px",
                      textAlign: "left",
                      fontFamily: "var(--font-body)",
                      fontSize: 11,
                      fontWeight: 600,
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      color: sortDir ? "var(--primary)" : "var(--text-muted)",
                      borderBottom: "1px solid var(--border-light)",
                      whiteSpace: "nowrap",
                      cursor: "pointer",
                      userSelect: "none",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      Name
                      {sortDir === "asc" ? (
                        <ChevronUp size={12} strokeWidth={2} color="var(--primary)" />
                      ) : sortDir === "desc" ? (
                        <ChevronDown size={12} strokeWidth={2} color="var(--primary)" />
                      ) : (
                        <ChevronsUpDown size={12} strokeWidth={1.5} color="var(--text-muted)" />
                      )}
                    </div>
                  </th>
                  {["Roles", "Addresses"].map((h) => (
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
                {displayed.map((org: Organisation) => (
                  <tr
                    key={org.id}
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
                        {org.name}
                      </span>
                    </td>
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)" }}>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {org.tags.map((t) => (
                          <span key={t.tag} className={`chip ${TAG_CHIP[t.tag] ?? "chip-blue"}`}>
                            {ORG_TAG_LABELS[t.tag as OrgTag] ?? t.tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)", fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-secondary)" }}>
                      {org.addresses.length}
                    </td>
                    {canWrite && (
                      <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)", textAlign: "right" }}>
                        <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                          <button
                            onClick={() => navigate(`/master-data/organisations/${org.id}/edit`)}
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
                            onClick={() => handleDeactivate(org)}
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
                              onClick={() => handleHardDelete(org)}
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
