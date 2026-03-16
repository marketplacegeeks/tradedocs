// T&C Template list page — design system table layout (FR-07).

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { Modal, message } from "antd";

import { listTCTemplates, deleteTCTemplate } from "../../api/tcTemplates";
import type { TCTemplate } from "../../api/tcTemplates";
import { useAuth } from "../../store/AuthContext";
import { ROLES } from "../../utils/constants";

export default function TCTemplateListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canWrite = user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN;

  // Track which template is pending deletion confirmation.
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["tc-templates"],
    queryFn: listTCTemplates,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTCTemplate,
    onSuccess: () => {
      // Remove from cache so the row disappears immediately.
      queryClient.invalidateQueries({ queryKey: ["tc-templates"] });
      message.success("Template deactivated.");
      setDeletingId(null);
    },
    onError: () => {
      message.error("Failed to deactivate template. Please try again.");
      setDeletingId(null);
    },
  });

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
            {templates.length} template{templates.length !== 1 ? "s" : ""} available
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
        ) : templates.length === 0 ? (
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
              No templates yet
            </p>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: 13,
                color: "var(--text-muted)",
                margin: 0,
              }}
            >
              {canWrite
                ? 'Click "New Template" to create one.'
                : "No T&C templates have been added yet."}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 600 }}>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  {["Template Name", "Organisations", "Last Updated"].map((h) => (
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
                {templates.map((template: TCTemplate) => (
                  <tr
                    key={template.id}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLTableRowElement).style.background = "transparent";
                    }}
                  >
                    {/* Template name */}
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

                    {/* Organisation chips */}
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

                    {/* Last updated date */}
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

                    {/* Action buttons — only visible to Checker / Admin */}
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
