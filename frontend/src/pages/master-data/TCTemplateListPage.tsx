// T&C Template list page — design system table layout (FR-07).

import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Search, ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";
import { Modal, message } from "antd";

import { listTCTemplates, deleteTCTemplate } from "../../api/tcTemplates";
import type { TCTemplate } from "../../api/tcTemplates";
import { useAuth } from "../../store/AuthContext";
import { ROLES } from "../../utils/constants";

type SortKey = "name" | "updated_at";
type SortDir = "asc" | "desc" | null;
type SortConfig = { key: SortKey; dir: SortDir } | null;

export default function TCTemplateListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canWrite = user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN;

  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["tc-templates"],
    queryFn: listTCTemplates,
  });

  // Filter by name, then sort
  const displayed = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    let rows = q
      ? templates.filter((t: TCTemplate) => t.name.toLowerCase().includes(q))
      : templates;
    if (sortConfig?.dir) {
      rows = [...rows].sort((a, b) => {
        if (sortConfig.key === "updated_at") {
          const diff = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
          return sortConfig.dir === "asc" ? diff : -diff;
        }
        const av = a.name.toLowerCase();
        const bv = b.name.toLowerCase();
        return sortConfig.dir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      });
    }
    return rows;
  }, [templates, searchQuery, sortConfig]);

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

  const deleteMutation = useMutation({
    mutationFn: deleteTCTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tc-templates"] });
      message.success("Template deactivated.");
      setDeletingId(null);
    },
    onError: () => {
      message.error("Failed to deactivate template. Please try again.");
      setDeletingId(null);
    },
  });

  const countLabel = searchQuery.trim()
    ? `${displayed.length} of ${templates.length} template${templates.length !== 1 ? "s" : ""}`
    : `${templates.length} template${templates.length !== 1 ? "s" : ""} available`;

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
            T&amp;C Templates
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {countLabel}
          </p>
        </div>
        {canWrite && (
          <button
            onClick={() => navigate("/master-data/tc-templates/new")}
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
            New Template
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
          placeholder="Search templates…"
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
          <div
            style={{
              padding: 40,
              textAlign: "center",
              color: "var(--text-muted)",
              fontFamily: "var(--font-body)",
            }}
          >
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
            <p
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: 15,
                fontWeight: 600,
                color: "var(--text-primary)",
                margin: 0,
              }}
            >
              {searchQuery.trim() ? `No results for "${searchQuery.trim()}"` : "No templates yet"}
            </p>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: 13,
                color: "var(--text-muted)",
                margin: 0,
              }}
            >
              {searchQuery.trim()
                ? "Try a different search term."
                : canWrite
                ? 'Click "New Template" to create one.'
                : "No T&C templates have been added yet."}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 600 }}>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  <th onClick={() => toggleSort("name")} style={sortHeaderStyle("name")}>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      Template Name {sortIcon("name")}
                    </div>
                  </th>
                  <th
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
                    Organisations
                  </th>
                  <th onClick={() => toggleSort("updated_at")} style={sortHeaderStyle("updated_at")}>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      Last Updated {sortIcon("updated_at")}
                    </div>
                  </th>
                  {canWrite && (
                    <th
                      style={{
                        padding: "12px 16px",
                        borderBottom: "1px solid var(--border-light)",
                      }}
                    />
                  )}
                </tr>
              </thead>
              <tbody>
                {displayed.map((template: TCTemplate) => (
                  <tr
                    key={template.id}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLTableRowElement).style.background = "transparent";
                    }}
                  >
                    <td
                      style={{
                        padding: "14px 16px",
                        borderBottom: "1px solid var(--border-light)",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "var(--font-body)",
                          fontSize: 14,
                          fontWeight: 500,
                          color: "var(--text-primary)",
                        }}
                      >
                        {template.name}
                      </span>
                    </td>
                    <td
                      style={{
                        padding: "14px 16px",
                        borderBottom: "1px solid var(--border-light)",
                      }}
                    >
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                        {template.organisation_names.map((orgName) => (
                          <span key={orgName} className="chip chip-blue">
                            {orgName}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td
                      style={{
                        padding: "14px 16px",
                        borderBottom: "1px solid var(--border-light)",
                        fontFamily: "var(--font-body)",
                        fontSize: 13,
                        color: "var(--text-muted)",
                      }}
                    >
                      {new Date(template.updated_at).toLocaleDateString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </td>
                    {canWrite && (
                      <td
                        style={{
                          padding: "14px 16px",
                          borderBottom: "1px solid var(--border-light)",
                          textAlign: "right",
                        }}
                      >
                        <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                          <button
                            onClick={() =>
                              navigate(`/master-data/tc-templates/${template.id}/edit`)
                            }
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
                              ((e.currentTarget as HTMLButtonElement).style.background =
                                "var(--bg-hover)")
                            }
                            onMouseLeave={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background =
                                "transparent")
                            }
                          >
                            <Pencil size={12} strokeWidth={1.5} />
                            Edit
                          </button>
                          <button
                            onClick={() => setDeletingId(template.id)}
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
                              color: "var(--pastel-pink-text)",
                              cursor: "pointer",
                            }}
                            onMouseEnter={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background =
                                "var(--pastel-pink)")
                            }
                            onMouseLeave={(e) =>
                              ((e.currentTarget as HTMLButtonElement).style.background =
                                "transparent")
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

      {/* Soft-delete confirmation modal */}
      <Modal
        title="Deactivate Template"
        open={deletingId !== null}
        onOk={() => {
          if (deletingId !== null) deleteMutation.mutate(deletingId);
        }}
        onCancel={() => setDeletingId(null)}
        okText="Deactivate"
        okButtonProps={{ danger: true, loading: deleteMutation.isPending }}
        cancelText="Cancel"
      >
        <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-secondary)" }}>
          This template will be deactivated and will no longer appear in document dropdowns.
          Existing documents that use this template are not affected.
        </p>
      </Modal>
    </div>
  );
}
